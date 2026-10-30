from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.memberships.repository import (
    WorkspaceMembershipRepository,
)
from app.modules.workspaces.models import (
    MEMBERSHIP_STATUS_ACTIVE,
    WORKSPACE_ROLE_ADMIN,
    WORKSPACE_ROLE_OWNER,
)


class EmployeeMembershipBridge:
    """
    Control-plane authorization bridge for tenant Employee APIs.

    This class never accesses tenant employee tables.

    Responsibilities:

    - confirm caller belongs to workspace
    - confirm caller has OWNER/ADMIN management permission
    - validate optional Employee.user_id against workspace membership
    """

    def __init__(
        self,
        control_session: AsyncSession,
    ) -> None:
        self.repository = (
            WorkspaceMembershipRepository(
                control_session
            )
        )

    async def require_active_member(
        self,
        *,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
    ):
        membership = (
            await self.repository
            .get_active_for_user(
                workspace_id=workspace_id,
                user_id=user_id,
            )
        )

        if membership is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Active workspace membership "
                    "required."
                ),
            )

        if (
            membership.status
            != MEMBERSHIP_STATUS_ACTIVE
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Workspace membership is "
                    "not active."
                ),
            )

        return membership

    async def require_manager(
        self,
        *,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
    ):
        membership = (
            await self.require_active_member(
                workspace_id=workspace_id,
                user_id=user_id,
            )
        )

        if membership.role_key not in {
            WORKSPACE_ROLE_OWNER,
            WORKSPACE_ROLE_ADMIN,
        }:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Workspace OWNER or ADMIN "
                    "role required."
                ),
            )

        return membership

    async def validate_employee_user_link(
        self,
        *,
        workspace_id: uuid.UUID,
        employee_user_id: (
            uuid.UUID | None
        ),
    ):
        """
        Employee records may exist before login accounts exist.

        Therefore user_id=None is valid.

        When user_id exists, it must refer to an ACTIVE member of
        the same workspace.
        """

        if employee_user_id is None:
            return None

        membership = (
            await self.repository
            .get_active_for_user(
                workspace_id=workspace_id,
                user_id=employee_user_id,
            )
        )

        if membership is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "Employee user_id must belong "
                    "to an active member of this "
                    "workspace."
                ),
            )

        return membership