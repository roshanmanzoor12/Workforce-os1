from __future__ import annotations

import uuid
from dataclasses import dataclass

from fastapi import (
    HTTPException,
    status,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.modules.employees.models import (
    Employee,
)
from app.modules.employees.repository import (
    EmployeeRepository,
)
from app.modules.leave.permissions import (
    LEAVE_ALL_READ,
    LEAVE_APPROVE,
    LEAVE_BALANCE_MANAGE,
    LEAVE_MANAGE,
    LEAVE_POLICY_MANAGE,
    LEAVE_SELF_READ,
    LEAVE_TEAM_READ,
)
from app.modules.workspace_permissions.service import (
    WorkspacePermissionService,
)


@dataclass(
    frozen=True,
    slots=True,
)
class LeaveTargetAccess:
    actor_employee_id: (
        uuid.UUID | None
    )

    target_employee_id: uuid.UUID

    is_self: bool
    is_team: bool
    is_all: bool


class LeaveAccessService:
    """
    Tenant-local leave target scope enforcement.

    Scope rules:

        self
            actor Employee == target Employee

        team
            target is direct report
            OR target shares actor's non-null team

        all
            workspace-wide leave read permission

    Permission authority remains WorkspacePermissionService.
    """

    def __init__(
        self,
        *,
        tenant_session: AsyncSession,
        actor_user_id: uuid.UUID,
        permission_service: (
            WorkspacePermissionService
        ),
    ) -> None:
        self.session = tenant_session

        self.actor_user_id = (
            actor_user_id
        )

        self.permissions = (
            permission_service
        )

        self.employees = (
            EmployeeRepository(
                tenant_session
            )
        )

    # =====================================================
    # EMPLOYEE RESOLUTION
    # =====================================================

    async def actor_employee(
        self,
    ) -> Employee | None:
        return await (
            self.employees
            .get_employee_by_user_id(
                self.actor_user_id
            )
        )

    async def require_self_employee(
        self,
    ) -> Employee:
        self.permissions.require(
            LEAVE_SELF_READ
        )

        employee = await (
            self.actor_employee()
        )

        if (
            employee is None
            or not employee.is_active
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Active employee record "
                    "not found for current user."
                ),
            )

        return employee

    async def require_employee(
        self,
        employee_id: uuid.UUID,
    ) -> Employee:
        employee = await (
            self.employees
            .get_employee_by_id(
                employee_id
            )
        )

        if (
            employee is None
            or not employee.is_active
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Active employee "
                    "not found."
                ),
            )

        return employee

    # =====================================================
    # TARGET SCOPE
    # =====================================================

    async def resolve_target_access(
        self,
        *,
        employee_id: uuid.UUID,
    ) -> LeaveTargetAccess:
        target = await (
            self.require_employee(
                employee_id
            )
        )

        if self.permissions.has(
            LEAVE_ALL_READ
        ):
            actor = await (
                self.actor_employee()
            )

            return LeaveTargetAccess(
                actor_employee_id=(
                    actor.id
                    if actor
                    else None
                ),
                target_employee_id=(
                    target.id
                ),
                is_self=(
                    actor is not None
                    and actor.id
                    == target.id
                ),
                is_team=True,
                is_all=True,
            )

        actor = await (
            self.actor_employee()
        )

        if (
            actor is None
            or not actor.is_active
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_403_FORBIDDEN
                ),
                detail=(
                    "Leave target scope "
                    "is unavailable."
                ),
            )

        is_self = (
            actor.id
            == target.id
        )

        is_direct_report = (
            target.manager_id
            == actor.id
        )

        same_team = (
            actor.team_id is not None
            and target.team_id
            == actor.team_id
        )

        return LeaveTargetAccess(
            actor_employee_id=(
                actor.id
            ),
            target_employee_id=(
                target.id
            ),
            is_self=is_self,
            is_team=(
                is_direct_report
                or same_team
            ),
            is_all=False,
        )

    async def require_leave_read(
        self,
        *,
        employee_id: uuid.UUID,
    ) -> LeaveTargetAccess:
        access = await (
            self.resolve_target_access(
                employee_id=employee_id
            )
        )

        if access.is_all:
            return access

        if (
            access.is_self
            and self.permissions.has(
                LEAVE_SELF_READ
            )
        ):
            return access

        if (
            access.is_team
            and self.permissions.has(
                LEAVE_TEAM_READ
            )
        ):
            return access

        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=(
                "Leave target is outside "
                "the permitted scope."
            ),
        )

    async def require_leave_approval(
        self,
        *,
        employee_id: uuid.UUID,
    ) -> LeaveTargetAccess:
        self.permissions.require(
            LEAVE_APPROVE
        )

        access = await (
            self.resolve_target_access(
                employee_id=employee_id
            )
        )

        if access.is_all:
            return access

        if (
            access.is_team
            and self.permissions.has(
                LEAVE_TEAM_READ
            )
        ):
            return access

        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=(
                "Leave request is outside "
                "the approver's scope."
            ),
        )

    # =====================================================
    # MANAGEMENT
    # =====================================================

    def require_manage(
        self,
    ) -> None:
        self.permissions.require(
            LEAVE_MANAGE
        )

    def require_policy_manage(
        self,
    ) -> None:
        self.permissions.require(
            LEAVE_POLICY_MANAGE
        )

    def require_balance_manage(
        self,
    ) -> None:
        self.permissions.require(
            LEAVE_BALANCE_MANAGE
        )


__all__ = [
    "LeaveTargetAccess",
    "LeaveAccessService",
]