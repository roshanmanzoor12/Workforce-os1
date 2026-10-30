from __future__ import annotations

from app.modules.workspace_permissions.access_context import (
    WorkspaceAccessContext,
)
from app.modules.workspace_permissions.saved_scopes import (
    resolve_saved_scope_access,
)


async def resolve_request_saved_scopes(
    scope: object,
    context: WorkspaceAccessContext,
) -> WorkspaceAccessContext:
    """
    Load saved scopes using the caller's authorized control session.

    Older internal callers without a control session retain their
    existing access context and receive no additional saved grants.

    HTTP tenant scopes and EmployeeAccessService supply the control
    session explicitly.
    """
    control_session = getattr(scope, "control_session", None)

    if control_session is None:
        return context

    return await resolve_saved_scope_access(
        control_session,
        tenant_scope=scope,
        context=context,
    )


__all__ = ["resolve_request_saved_scopes"]