from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.workspaces.models import (
    Workspace,
    WorkspaceMembership,
    MEMBERSHIP_STATUS_ACTIVE,
    WORKSPACE_ROLE_ADMIN,
    WORKSPACE_ROLE_OWNER,
)
from app.modules.organizations.schemas import (
    OrganizationUpdateRequest,
)


class OrganizationService:
    def __init__(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
    ) -> None:
        self.session = session
        self.user_id = user_id

    async def get_organization(
        self,
        organization_id: uuid.UUID,
    ) -> Workspace:
        workspace = await self._authorized_workspace(
            organization_id
        )

        return workspace

    async def update_organization(
        self,
        organization_id: uuid.UUID,
        request: OrganizationUpdateRequest,
    ) -> Workspace:
        workspace, membership = await (
            self._authorized_workspace_with_membership(
                organization_id
            )
        )

        if membership.role_key not in {
            WORKSPACE_ROLE_OWNER,
            WORKSPACE_ROLE_ADMIN,
        }:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Organization management permission "
                    "is required."
                ),
            )

        values = request.model_dump(
            exclude_unset=True
        )

        for field, value in values.items():
            setattr(workspace, field, value)

        await self.session.commit()
        await self.session.refresh(workspace)

        return workspace

    async def list_workspaces(
        self,
        organization_id: uuid.UUID,
    ) -> list[Workspace]:
        await self._authorized_workspace(
            organization_id
        )

        result = await self.session.execute(
            select(Workspace)
            .join(
                WorkspaceMembership,
                WorkspaceMembership.workspace_id
                == Workspace.id,
            )
            .where(
                WorkspaceMembership.user_id
                == self.user_id,
                WorkspaceMembership.status
                == MEMBERSHIP_STATUS_ACTIVE,
                Workspace.is_active.is_(True),
            )
            .order_by(Workspace.name.asc())
        )

        return list(result.scalars().unique().all())

    async def _authorized_workspace(
        self,
        organization_id: uuid.UUID,
    ) -> Workspace:
        workspace, _ = await (
            self._authorized_workspace_with_membership(
                organization_id
            )
        )

        return workspace

    async def _authorized_workspace_with_membership(
        self,
        organization_id: uuid.UUID,
    ) -> tuple[
        Workspace,
        WorkspaceMembership,
    ]:
        result = await self.session.execute(
            select(
                Workspace,
                WorkspaceMembership,
            )
            .join(
                WorkspaceMembership,
                WorkspaceMembership.workspace_id
                == Workspace.id,
            )
            .where(
                Workspace.id == organization_id,
                WorkspaceMembership.user_id
                == self.user_id,
                WorkspaceMembership.status
                == MEMBERSHIP_STATUS_ACTIVE,
                Workspace.is_active.is_(True),
            )
        )

        row = result.one_or_none()

        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found.",
            )

        return row


__all__ = [
    "OrganizationService",
]