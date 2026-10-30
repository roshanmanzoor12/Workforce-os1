from __future__ import annotations

import uuid

from fastapi import HTTPException, WebSocketException
from starlette.requests import HTTPConnection

from app.core.database import ControlSessionLocal
from app.modules.auth.permissions import bearer_scheme, get_current_user, require_verified_email
from .workspace_billing import require_workspace_access
from .payment_policy import workspace_cleanup_route


def guarded_workspace(path: str, method: str, params: dict):
    """Use the matched route template, not a user-supplied workspace query."""
    parts = path.strip('/').split('/')
    if 'billing' in parts or 'workspaces' not in parts or 'workspace_id' not in params:
        return None
    index = parts.index('workspaces')
    tail = parts[index + 2:]
    # These supplied OpenAPI routes authenticate with WorkspaceAPIKey, not
    # the user's bearer token. Preserve their existing authentication. Their
    # own authenticated dependency needs a separate billing audit.
    if tail and tail[0] in {'integrations', 'api-key-auth'}:
        return None
    # Allow only the selector's basic workspace metadata. Workspace contents,
    # bootstrap, and mutations remain gated. Billing has its own membership check.
    if method == 'GET' and len(parts) == index + 2:
        return None
    if workspace_cleanup_route(path, method):
        return None
    return uuid.UUID(str(params['workspace_id']))


async def enforce_workspace_subscription(connection: HTTPConnection):
    route = connection.scope.get('route')
    workspace_id = guarded_workspace(
        getattr(route, 'path', ''), connection.scope.get('method', 'WEBSOCKET'),
        connection.path_params,
    )
    if workspace_id is None:
        return
    try:
        async with ControlSessionLocal() as db:
            credentials = await bearer_scheme(connection)
            user = await get_current_user(credentials, db)
            require_verified_email(user)
            await require_workspace_access(db, workspace_id, user.id)
    except HTTPException:
        if connection.scope['type'] == 'websocket':
            raise WebSocketException(code=1008, reason='Workspace access unavailable.')
        raise
