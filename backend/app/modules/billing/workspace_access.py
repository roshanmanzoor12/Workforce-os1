from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from .entitlements import AccountEntitlements
from .workspace_count import (
    count_owned_active_workspaces,
)
from .workspace_guard import WorkspaceCreationGuard


class WorkspaceEntitlementAccess:
    def __init__(
        self,
        session: AsyncSession,
        *,
        guard: WorkspaceCreationGuard | None = None,
    ) -> None:
        self.session = session

        self.guard = (
            guard
            or WorkspaceCreationGuard()
        )

    async def require_workspace_creation(
        self,
        *,
        user_id: uuid.UUID,
    ) -> AccountEntitlements:
        return await self.guard.require_allowed(
            self.session,
            user_id=user_id,
            workspace_count_loader=(
                count_owned_active_workspaces
            ),
        )


def get_workspace_entitlement_access(
    session: AsyncSession,
) -> WorkspaceEntitlementAccess:
    return WorkspaceEntitlementAccess(
        session
    )


__all__ = [
    "WorkspaceEntitlementAccess",
    "get_workspace_entitlement_access",
]