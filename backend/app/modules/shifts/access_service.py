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
    Team,
)
from app.modules.employees.repository import (
    EmployeeRepository,
)
from app.modules.workspace_permissions.permissions import (
    WorkspacePermission,
)
from app.modules.workspace_permissions.service import (
    WorkspacePermissionService,
)


@dataclass(
    frozen=True,
    slots=True,
)
class ScheduleTargetAccess:
    actor_employee_id: (
        uuid.UUID | None
    )

    target_employee_id: uuid.UUID

    is_self: bool
    is_team: bool
    is_all: bool


class ShiftAccessService:
    """
    Permission + target-scope enforcement for scheduling.

    Tenant isolation is already provided by TenantScope.

    This service answers a different question:

        May the authenticated workspace member access
        THIS employee/team target?
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
        self.employee_repository = (
            EmployeeRepository(
                tenant_session
            )
        )

        self.actor_user_id = (
            actor_user_id
        )

        self.permissions = (
            permission_service
        )

    # =====================================================
    # ACTOR
    # =====================================================

    async def get_actor_employee(
        self,
    ) -> Employee | None:
        return await (
            self.employee_repository
            .get_employee_by_user_id(
                self.actor_user_id
            )
        )

    # =====================================================
    # TARGET LOOKUP
    # =====================================================

    async def require_target_employee(
        self,
        *,
        employee_id: uuid.UUID,
    ) -> Employee:
        employee = await (
            self.employee_repository
            .get_employee_by_id(
                employee_id
            )
        )

        if employee is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail="Employee not found.",
            )

        return employee

    async def require_target_team(
        self,
        *,
        team_id: uuid.UUID,
    ) -> Team:
        team = await (
            self.employee_repository
            .get_team_by_id(
                team_id
            )
        )

        if team is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail="Team not found.",
            )

        return team

    # =====================================================
    # PURE SCOPE RULES
    # =====================================================

    @staticmethod
    def is_self_target(
        *,
        actor: Employee | None,
        target: Employee,
    ) -> bool:
        if actor is None:
            return False

        return actor.id == target.id

    @staticmethod
    def is_team_target(
        *,
        actor: Employee | None,
        target: Employee,
    ) -> bool:
        """
        Current WorkforceOS organization model supports:

        - explicit direct-report scope via manager_id
        - same-team scope via team_id

        Self is deliberately handled separately.
        """

        if actor is None:
            return False

        if actor.id == target.id:
            return False

        if (
            target.manager_id
            == actor.id
        ):
            return True

        if (
            actor.team_id is not None
            and target.team_id
            == actor.team_id
        ):
            return True

        return False

    # =====================================================
    # EMPLOYEE SCHEDULE READ
    # =====================================================

    async def require_schedule_read(
        self,
        *,
        employee_id: uuid.UUID,
    ) -> ScheduleTargetAccess:
        target = await (
            self.require_target_employee(
                employee_id=employee_id
            )
        )

        # -------------------------------------------------
        # ALL
        # -------------------------------------------------

        if self.permissions.has(
            WorkspacePermission
            .SHIFTS_ALL_READ
            .value
        ):
            actor = await (
                self.get_actor_employee()
            )

            return ScheduleTargetAccess(
                actor_employee_id=(
                    actor.id
                    if actor is not None
                    else None
                ),
                target_employee_id=(
                    target.id
                ),
                is_self=(
                    actor is not None
                    and actor.id == target.id
                ),
                is_team=False,
                is_all=True,
            )

        actor = await (
            self.get_actor_employee()
        )

        # -------------------------------------------------
        # SELF
        # -------------------------------------------------

        if (
            self.permissions.has(
                WorkspacePermission
                .SHIFTS_SELF_READ
                .value
            )
            and self.is_self_target(
                actor=actor,
                target=target,
            )
        ):
            return ScheduleTargetAccess(
                actor_employee_id=(
                    actor.id
                    if actor is not None
                    else None
                ),
                target_employee_id=(
                    target.id
                ),
                is_self=True,
                is_team=False,
                is_all=False,
            )

        # -------------------------------------------------
        # TEAM
        # -------------------------------------------------

        if (
            self.permissions.has(
                WorkspacePermission
                .SHIFTS_TEAM_READ
                .value
            )
            and self.is_team_target(
                actor=actor,
                target=target,
            )
        ):
            return ScheduleTargetAccess(
                actor_employee_id=(
                    actor.id
                    if actor is not None
                    else None
                ),
                target_employee_id=(
                    target.id
                ),
                is_self=False,
                is_team=True,
                is_all=False,
            )

        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=(
                "Schedule target is outside "
                "the authorized scope."
            ),
        )

    # =====================================================
    # MY SCHEDULE
    # =====================================================

    async def require_self_employee(
        self,
    ) -> Employee:
        if not self.permissions.has(
            WorkspacePermission
            .SHIFTS_SELF_READ
            .value
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_403_FORBIDDEN
                ),
                detail=(
                    "Self schedule permission "
                    "is required."
                ),
            )

        employee = await (
            self.get_actor_employee()
        )

        if employee is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Authenticated user is "
                    "not linked to an employee."
                ),
            )

        return employee

    # =====================================================
    # TEAM ASSIGNMENT READ
    # =====================================================

    async def require_team_schedule_read(
        self,
        *,
        team_id: uuid.UUID,
    ) -> Team:
        team = await (
            self.require_target_team(
                team_id=team_id
            )
        )

        if self.permissions.has(
            WorkspacePermission
            .SHIFTS_ALL_READ
            .value
        ):
            return team

        if not self.permissions.has(
            WorkspacePermission
            .SHIFTS_TEAM_READ
            .value
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_403_FORBIDDEN
                ),
                detail=(
                    "Team schedule permission "
                    "is required."
                ),
            )

        actor = await (
            self.get_actor_employee()
        )

        if (
            actor is None
            or actor.team_id is None
            or actor.team_id != team_id
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_403_FORBIDDEN
                ),
                detail=(
                    "Team schedule target is "
                    "outside the authorized scope."
                ),
            )

        return team

    # =====================================================
    # MUTATION TARGET VALIDATION
    # =====================================================

    async def require_employee_target(
        self,
        *,
        employee_id: uuid.UUID,
    ) -> Employee:
        employee = await (
            self.employee_repository
            .get_employee_by_id(
                employee_id
            )
        )

        if employee is None:
            raise HTTPException(
                status_code=(
                    status
                    .HTTP_422_UNPROCESSABLE_ENTITY
                ),
                detail=(
                    "Shift assignment employee "
                    "does not exist."
                ),
            )

        if not employee.is_active:
            raise HTTPException(
                status_code=(
                    status
                    .HTTP_422_UNPROCESSABLE_ENTITY
                ),
                detail=(
                    "Shift assignment employee "
                    "is inactive."
                ),
            )

        return employee

    async def require_team_target(
        self,
        *,
        team_id: uuid.UUID,
    ) -> Team:
        team = await (
            self.employee_repository
            .get_team_by_id(
                team_id
            )
        )

        if team is None:
            raise HTTPException(
                status_code=(
                    status
                    .HTTP_422_UNPROCESSABLE_ENTITY
                ),
                detail=(
                    "Shift assignment team "
                    "does not exist."
                ),
            )

        if not team.is_active:
            raise HTTPException(
                status_code=(
                    status
                    .HTTP_422_UNPROCESSABLE_ENTITY
                ),
                detail=(
                    "Shift assignment team "
                    "is inactive."
                ),
            )

        return team


__all__ = [
    "ScheduleTargetAccess",
    "ShiftAccessService",
]