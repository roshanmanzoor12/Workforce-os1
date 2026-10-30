from __future__ import annotations

from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import User
from app.modules.workspaces.schemas import (
    WorkspaceCreateRequest,
    WorkspaceCreateResponse,
)

from .workspace_access import (
    WorkspaceEntitlementAccess,
)


class WorkspaceCreator(Protocol):
    async def create_workspace(
        self,
        request: WorkspaceCreateRequest,
        *,
        user: User,
    ) -> WorkspaceCreateResponse:
        ...


class WorkspaceCreationOrchestrator:
    def __init__(
        self,
        session: AsyncSession,
        *,
        entitlement_access: WorkspaceEntitlementAccess | None = None,
    ) -> None:
        self.session = session

        self.entitlement_access = (
            entitlement_access
            or WorkspaceEntitlementAccess(
                session
            )
        )

    async def create(
        self,
        request: WorkspaceCreateRequest,
        *,
        user: User,
        workspace_creator: WorkspaceCreator,
    ) -> WorkspaceCreateResponse:
        await self.entitlement_access.require_workspace_creation(
            user_id=user.id
        )

        return await workspace_creator.create_workspace(
            request,
            user=user,
        )


__all__ = [
    "WorkspaceCreationOrchestrator",
    "WorkspaceCreator",
]