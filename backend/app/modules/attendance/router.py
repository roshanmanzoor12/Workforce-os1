from __future__ import annotations

import uuid
from datetime import date

from fastapi import (
    APIRouter,
    Query,
    status,
)

from app.core.exceptions import (
    ValidationError,
)
from app.db.tenant_dependency import (
    TenantScope,
)
from app.modules.attendance.enums import (
    AttendanceStatus,
)
from app.modules.attendance.schemas import (
    AttendanceDayDetailResponse,
    AttendanceDayResponse,
    AttendanceDayUpdateRequest,
    AttendanceEventCreateRequest,
    AttendanceEventResponse,
    AttendanceListResponse,
    AttendanceSummaryResponse,
)
from app.modules.attendance.service import (
    AttendanceService,
)


# =========================================================
# ROUTER
# =========================================================


router = APIRouter(
    prefix=(
        "/workspaces/{workspace_id}/attendance"
    ),
    tags=["Attendance"],
)


# =========================================================
# RBAC
# =========================================================


ATTENDANCE_WRITE_ROLES = frozenset(
    {
        "owner",
        "admin",
    }
)


def get_scope_role(
    scope: TenantScope,
) -> str | None:
    """
    Resolve the trusted workspace role from TenantScope.

    Role information must never come from client input.
    """

    role_key = getattr(
        scope,
        "role_key",
        None,
    )

    if isinstance(
        role_key,
        str,
    ):
        return role_key

    context = getattr(
        scope,
        "context",
        None,
    )

    if context is None:
        return None

    role_key = getattr(
        context,
        "role_key",
        None,
    )

    if isinstance(
        role_key,
        str,
    ):
        return role_key

    return None


def get_scope_actor_user_id(
    scope: TenantScope,
) -> uuid.UUID | None:
    """
    Resolve authenticated global user id from trusted TenantScope.

    Attendance events keep actor attribution, but the actor id
    must never be accepted from request payload.
    """

    actor_user_id = getattr(
        scope,
        "actor_user_id",
        None,
    )

    if actor_user_id is None:
        context = getattr(
            scope,
            "context",
            None,
        )

        if context is not None:
            actor_user_id = getattr(
                context,
                "actor_user_id",
                None,
            )

    if actor_user_id is None:
        user = getattr(
            scope,
            "user",
            None,
        )

        if user is not None:
            actor_user_id = getattr(
                user,
                "id",
                None,
            )

    if actor_user_id is None:
        return None

    if isinstance(
        actor_user_id,
        uuid.UUID,
    ):
        return actor_user_id

    try:
        return uuid.UUID(
            str(actor_user_id)
        )

    except (
        TypeError,
        ValueError,
    ):
        return None


def require_attendance_write_access(
    scope: TenantScope,
) -> None:
    """
    Administrative attendance record correction requires
    workspace OWNER or ADMIN.

    Normal attendance event recording remains available through
    the authorized tenant scope.
    """

    role_key = get_scope_role(
        scope
    )

    if (
        role_key
        not in ATTENDANCE_WRITE_ROLES
    ):
        raise ValidationError(
            "Owner or admin workspace role "
            "is required to modify "
            "attendance records."
        )


# =========================================================
# SERVICE FACTORY
# =========================================================


def get_attendance_service(
    scope: TenantScope,
) -> AttendanceService:
    """
    Build AttendanceService from the already-authorized
    tenant AsyncSession.
    """

    return AttendanceService(
        scope.session
    )


# =========================================================
# ATTENDANCE EVENTS
# =========================================================


@router.post(
    "/employees/{employee_id}/events",
    response_model=AttendanceEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record attendance event",
)
async def record_attendance_event(
    employee_id: uuid.UUID,
    payload: AttendanceEventCreateRequest,
    scope: TenantScope,
) -> AttendanceEventResponse:
    service = get_attendance_service(
        scope
    )

    return await service.record_event(
        employee_id=employee_id,
        actor_user_id=(
            get_scope_actor_user_id(
                scope
            )
        ),
        request=payload,
    )


# =========================================================
# ATTENDANCE RECORDS
# =========================================================


@router.get(
    "/records",
    response_model=AttendanceListResponse,
    status_code=status.HTTP_200_OK,
    summary="List attendance records",
)
async def list_attendance_records(
    scope: TenantScope,
    employee_id: (
        uuid.UUID | None
    ) = Query(
        default=None,
    ),
    start_date: (
        date | None
    ) = Query(
        default=None,
    ),
    end_date: (
        date | None
    ) = Query(
        default=None,
    ),
    attendance_status: (
        AttendanceStatus | None
    ) = Query(
        default=None,
        alias="status",
    ),
) -> AttendanceListResponse:
    service = get_attendance_service(
        scope
    )

    return await service.list_days(
        employee_id=employee_id,
        start_date=start_date,
        end_date=end_date,
        status=attendance_status,
    )


@router.get(
    "/records/{attendance_record_id}",
    response_model=(
        AttendanceDayDetailResponse
    ),
    status_code=status.HTTP_200_OK,
    summary="Get attendance record",
)
async def get_attendance_record(
    attendance_record_id: uuid.UUID,
    scope: TenantScope,
) -> AttendanceDayDetailResponse:
    service = get_attendance_service(
        scope
    )

    return await service.get_day(
        attendance_day_id=(
            attendance_record_id
        ),
    )


@router.patch(
    "/records/{attendance_record_id}",
    response_model=AttendanceDayResponse,
    status_code=status.HTTP_200_OK,
    summary="Update attendance record",
)
async def update_attendance_record(
    attendance_record_id: uuid.UUID,
    payload: AttendanceDayUpdateRequest,
    scope: TenantScope,
) -> AttendanceDayResponse:
    require_attendance_write_access(
        scope
    )

    service = get_attendance_service(
        scope
    )

    return await service.update_day(
        payload,
        attendance_day_id=(
            attendance_record_id
        ),
    )


# =========================================================
# ATTENDANCE SUMMARY
# =========================================================


@router.get(
    "/employees/{employee_id}/summary",
    response_model=AttendanceSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get employee attendance summary",
)
async def get_employee_attendance_summary(
    employee_id: uuid.UUID,
    scope: TenantScope,
    start_date: date = Query(
        ...,
    ),
    end_date: date = Query(
        ...,
    ),
) -> AttendanceSummaryResponse:
    service = get_attendance_service(
        scope
    )

    return await service.employee_summary(
        employee_id=employee_id,
        start_date=start_date,
        end_date=end_date,
    )


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "ATTENDANCE_WRITE_ROLES",
    "get_scope_role",
    "get_scope_actor_user_id",
    "require_attendance_write_access",
    "get_attendance_service",
    "router",
]