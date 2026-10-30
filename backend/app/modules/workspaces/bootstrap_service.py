from __future__ import annotations

import uuid
from typing import Any

from app.modules.auth.models import User
from app.modules.workspace_permissions.effective import resolve_membership_access
from app.modules.workspaces.bootstrap_schemas import WorkspaceBootstrapResponse
from app.modules.workspaces.service import WorkspaceService


def _dump_model(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    # ORM objects can include relationships; return only scalar attributes.
    result: dict[str, Any] = {}
    for field in ("id", "workspace_id", "user_id", "role_key", "status", "name", "slug"):
        item = getattr(value, field, None)
        if isinstance(item, uuid.UUID):
            result[field] = str(item)
        elif isinstance(item, (str, int, float, bool)) or item is None:
            result[field] = item
    return result


class WorkspaceBootstrapService:
    def __init__(self, workspace_service: WorkspaceService) -> None:
        self.workspace_service = workspace_service

    async def get_workspace_bootstrap(
        self, *, workspace_id: uuid.UUID, user: User
    ) -> WorkspaceBootstrapResponse:
        workspace, membership, tenant = (
            await self.workspace_service.get_authorized_workspace_context(
                workspace_id=workspace_id, user=user
            )
        )
        # Resolve from trusted DB records, including additional/custom roles
        # and moderation bans. Never infer effective authority from the UI.
        access = await resolve_membership_access(
            self.workspace_service.session,
            workspace_id=workspace_id,
            membership=membership,
        )
        role_key = str(membership.role_key)
        permissions = sorted(access.permissions)
        return WorkspaceBootstrapResponse(
            workspace_id=str(workspace_id),
            membership_id=str(membership.id),
            role_key=role_key,
            permissions=permissions,
            moderation={
                "is_muted": False,
                "is_deafened": False,
                "is_hidden": False,
                "is_banned": False,
            },
            available_roles=[],
            workspace=_dump_model(workspace),
            membership=_dump_model(membership),
            roles=list(access.role_keys),
            scopes=[],
            entitlements={
                "workspace_id": str(workspace_id),
                "tenant_available": tenant is not None,
            },
            navigation=sorted({p.split(".", 1)[0] for p in permissions}),
            setup_status={
                "tenant_registered": tenant is not None,
                "workspace_status": str(workspace.status),
            },
        )


__all__ = ["WorkspaceBootstrapService"]
