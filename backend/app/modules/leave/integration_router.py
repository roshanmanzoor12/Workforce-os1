from __future__ import annotations

import uuid
from datetime import date

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    status,
)

from app.db.tenant_dependency import (
    TenantScope,
)
from app.modules.employees.repository import (
    EmployeeRepository,
)
from app.modules.leave.attendance_context import (
    LeaveAttendanceContextService,
)
from app.modules.leave.calendar_query import (
    LeaveCalendarQueryService,
)
from app.modules.leave.calendar_schemas import (
    LeaveCalendarResponse,
    LeaveConsumptionDayResponse,
)
from app.modules.leave.consumption import (
    LeaveConsumptionService,
)
from app.modules.leave.integration_schemas import (
    LeaveAttendanceContextResponse,
    PayrollLeavePeriodResponse,
)
from app.modules.leave.models import (
    LeaveRequestStatus,
)
from app.modules.leave.payroll_context import (
    LeavePayrollContextService,
)
from app.modules.workspace_permissions.permissions import (
    WorkspacePermission,
)
from app.modules.workspace_permissions.service import (
    WorkspacePermissionService,
)


router = APIRouter(
    prefix=(
        "/workspaces/{workspace_id}"
        "/leave-integration"
    ),
    tags=[
        "Leave Integration",
    ],
)


# =========================================================
# BASIC HELPERS
# =========================================================


def _permissions(
    scope: object,
) -> WorkspacePermissionService:
    return WorkspacePermissionService(
        scope
    )


def _validate_range(
    *,
    start_date: date,
    end_date: date,
) -> None:
    if end_date < start_date:
        raise HTTPException(
            status_code=(
                status
                .HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=(
                "end_date cannot be "
                "before start_date."
            ),
        )

    if (
        end_date - start_date
    ).days > 366:
        raise HTTPException(
            status_code=(
                status
                .HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=(
                "Date range cannot exceed "
                "367 days."
            ),
        )


# =========================================================
# TARGET EXISTENCE
# =========================================================


async def _require_employee(
    scope: object,
    employee_id: uuid.UUID,
):
    repository = EmployeeRepository(
        scope.session
    )

    employee = await (
        repository
        .get_employee_by_id(
            employee_id
        )
    )

    if employee is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Employee not found."
            ),
        )

    return employee


# =========================================================
# LEAVE READ SCOPE
# =========================================================


async def _require_employee_leave_read(
    scope: object,
    employee_id: uuid.UUID,
):
    """
    Effective Leave target scope:

        SELF
            LEAVE_SELF_READ

        TEAM
            LEAVE_TEAM_READ
            and target is direct report
            or belongs to same non-null team

        ALL
            LEAVE_ALL_READ

    The tenant session itself is already workspace-isolated by
    TenantScope.
    """

    permissions = _permissions(
        scope
    )

    repository = EmployeeRepository(
        scope.session
    )

    target = await (
        repository
        .get_employee_by_id(
            employee_id
        )
    )

    if target is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Employee not found."
            ),
        )

    # -----------------------------------------------------
    # ALL
    # -----------------------------------------------------

    if permissions.has(
        WorkspacePermission
        .LEAVE_ALL_READ
        .value
    ):
        return target

    actor = await (
        repository
        .get_employee_by_user_id(
            scope.user_id
        )
    )

    # -----------------------------------------------------
    # SELF
    # -----------------------------------------------------

    if (
        actor is not None
        and actor.id == target.id
        and permissions.has(
            WorkspacePermission
            .LEAVE_SELF_READ
            .value
        )
    ):
        return target

    # -----------------------------------------------------
    # TEAM
    # -----------------------------------------------------

    if (
        actor is not None
        and permissions.has(
            WorkspacePermission
            .LEAVE_TEAM_READ
            .value
        )
    ):
        direct_report = (
            target.manager_id
            == actor.id
        )

        same_team = (
            actor.team_id is not None
            and target.team_id
            is not None
            and actor.team_id
            == target.team_id
        )

        if (
            direct_report
            or same_team
        ):
            return target

    raise HTTPException(
        status_code=(
            status.HTTP_403_FORBIDDEN
        ),
        detail=(
            "Leave data is outside "
            "the permitted employee scope."
        ),
    )


# =========================================================
# EMPLOYEE LEAVE CALENDAR
# =========================================================


@router.get(
    (
        "/employees/{employee_id}"
        "/calendar"
    ),
    response_model=(
        LeaveCalendarResponse
    ),
)
async def employee_leave_calendar(
    employee_id: uuid.UUID,
    scope: TenantScope,
    start_date: date = Query(
        ...
    ),
    end_date: date = Query(
        ...
    ),
    request_status: (
        LeaveRequestStatus | None
    ) = Query(
        default=None,
        alias="status",
    ),
):
    _validate_range(
        start_date=start_date,
        end_date=end_date,
    )

    await _require_employee_leave_read(
        scope,
        employee_id,
    )

    return await (
        LeaveCalendarQueryService(
            scope.session
        )
        .employee_calendar(
            employee_id=employee_id,
            start_date=start_date,
            end_date=end_date,
            status=request_status,
        )
    )


# =========================================================
# ATTENDANCE CONTEXT
# =========================================================


@router.get(
    (
        "/employees/{employee_id}"
        "/attendance-context/"
        "{attendance_date}"
    ),
    response_model=(
        LeaveAttendanceContextResponse
    ),
)
async def employee_leave_attendance_context(
    employee_id: uuid.UUID,
    attendance_date: date,
    scope: TenantScope,
):
    await _require_employee_leave_read(
        scope,
        employee_id,
    )

    result = await (
        LeaveAttendanceContextService(
            scope.session
        )
        .for_employee_date(
            employee_id=employee_id,
            attendance_date=(
                attendance_date
            ),
        )
    )

    return (
        LeaveAttendanceContextResponse
        .model_validate(
            result
        )
    )


# =========================================================
# RAW LEAVE CONSUMPTION
# =========================================================


@router.get(
    (
        "/employees/{employee_id}"
        "/consumption/{leave_date}"
    ),
    response_model=(
        LeaveConsumptionDayResponse
    ),
)
async def employee_leave_consumption(
    employee_id: uuid.UUID,
    leave_date: date,
    scope: TenantScope,
):
    await _require_employee_leave_read(
        scope,
        employee_id,
    )

    result = await (
        LeaveConsumptionService(
            scope.session
        )
        .for_employee_date(
            employee_id=employee_id,
            leave_date=leave_date,
        )
    )

    return (
        LeaveConsumptionDayResponse
        .model_validate(
            result
        )
    )


# =========================================================
# PAYROLL CONTEXT
# =========================================================


@router.get(
    (
        "/employees/{employee_id}"
        "/payroll-context"
    ),
    response_model=(
        PayrollLeavePeriodResponse
    ),
)
async def employee_leave_payroll_context(
    employee_id: uuid.UUID,
    scope: TenantScope,
    start_date: date = Query(
        ...
    ),
    end_date: date = Query(
        ...
    ),
):
    _validate_range(
        start_date=start_date,
        end_date=end_date,
    )

    permissions = _permissions(
        scope
    )

    permissions.require_any(
        {
            WorkspacePermission
            .PAYROLL_READ
            .value,

            WorkspacePermission
            .PAYROLL_MANAGE
            .value,

            WorkspacePermission
            .LEAVE_ALL_READ
            .value,
        }
    )

    await _require_employee(
        scope,
        employee_id,
    )

    result = await (
        LeavePayrollContextService(
            scope.session
        )
        .for_period(
            employee_id=employee_id,
            period_start=start_date,
            period_end=end_date,
        )
    )

    return (
        PayrollLeavePeriodResponse
        .model_validate(
            result
        )
    )


__all__ = [
    "router",
]