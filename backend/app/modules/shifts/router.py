from __future__ import annotations

import uuid
from datetime import (
    date,
    timedelta,
)

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    Response,
    status,
)

from app.db.tenant_dependency import (
    ControlDB,
    TenantScope,
)
from app.modules.shifts.access_service import (
    ShiftAccessService,
)
from app.modules.shifts.audit import (
    audit_schedule_published,
)
from app.modules.shifts.models import (
    ShiftAssignmentTargetType,
)
from app.modules.shifts.publication_snapshot import (
    SchedulePublicationSnapshotService,
)
from app.modules.shifts.schemas import (
    ResolvedScheduleDayResponse,
    ScheduleExceptionCreateRequest,
    ScheduleExceptionResponse,
    ScheduleExceptionUpdateRequest,
    SchedulePublicationResponse,
    SchedulePublishRequest,
    ShiftAssignmentCreateRequest,
    ShiftAssignmentResponse,
    ShiftAssignmentUpdateRequest,
    ShiftCreateRequest,
    ShiftDetailResponse,
    ShiftResponse,
    ShiftUpdateRequest,
)
from app.modules.shifts.service import (
    ShiftService,
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
    ),
    tags=["Shifts"],
)


# =========================================================
# HELPERS
# =========================================================


def permission_service(
    scope: TenantScope,
) -> WorkspacePermissionService:
    return WorkspacePermissionService(
        scope
    )


def access_service(
    scope: TenantScope,
) -> ShiftAccessService:
    permissions = (
        permission_service(
            scope
        )
    )

    return ShiftAccessService(
        tenant_session=scope.session,
        actor_user_id=scope.user_id,
        permission_service=permissions,
    )


def validate_schedule_range(
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
        end_date
        - start_date
    ).days > 92:
        raise HTTPException(
            status_code=(
                status
                .HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=(
                "Schedule query cannot "
                "exceed 92 days."
            ),
        )


async def resolve_schedule_range(
    *,
    service: ShiftService,
    employee_id: uuid.UUID,
    start_date: date,
    end_date: date,
) -> list[
    ResolvedScheduleDayResponse
]:
    """
    Resolve a schedule range using immutable published snapshots
    whenever one exists.

    Resolution order per day:

        published snapshot
            ↓
        live schedule resolution
            ↓
        holiday context

    The snapshot service owns that decision so all schedule
    consumers receive the same authoritative result.
    """

    current_date = start_date

    result: list[
        ResolvedScheduleDayResponse
    ] = []

    resolver = (
        SchedulePublicationSnapshotService(
            service.session
        )
    )

    while (
        current_date
        <= end_date
    ):
        result.append(
            await resolver.resolve_day(
                employee_id=(
                    employee_id
                ),
                schedule_date=(
                    current_date
                ),
            )
        )

        current_date += timedelta(
            days=1
        )

    return result


# =========================================================
# SHIFTS
# =========================================================


@router.get(
    "/shifts",
    response_model=list[
        ShiftResponse
    ],
)
async def list_shifts(
    scope: TenantScope,
    active_only: bool = Query(
        default=False
    ),
):
    permission_service(
        scope
    ).require_any(
        {
            WorkspacePermission
            .SHIFTS_VIEW
            .value,

            WorkspacePermission
            .SHIFTS_ALL_READ
            .value,
        }
    )

    return await ShiftService(
        scope.session
    ).list_shifts(
        active_only=active_only
    )


@router.post(
    "/shifts",
    response_model=ShiftResponse,
    status_code=(
        status.HTTP_201_CREATED
    ),
)
async def create_shift(
    request: ShiftCreateRequest,
    scope: TenantScope,
):
    permission_service(
        scope
    ).require(
        WorkspacePermission
        .SHIFTS_MANAGE
        .value
    )

    return await ShiftService(
        scope.session
    ).create_shift(
        request
    )


@router.get(
    "/shifts/{shift_id}",
    response_model=(
        ShiftDetailResponse
    ),
)
async def get_shift(
    shift_id: uuid.UUID,
    scope: TenantScope,
):
    permission_service(
        scope
    ).require_any(
        {
            WorkspacePermission
            .SHIFTS_VIEW
            .value,

            WorkspacePermission
            .SHIFTS_ALL_READ
            .value,
        }
    )

    service = ShiftService(
        scope.session
    )

    shift = await (
        service.repository
        .get_shift(
            shift_id=shift_id
        )
    )

    if shift is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail="Shift not found.",
        )

    working_days = await (
        service.repository
        .list_working_days(
            shift_id=shift.id
        )
    )

    payload = (
        ShiftDetailResponse
        .model_validate(
            shift
        )
    )

    payload.working_days = [
        item
        for item
        in working_days
    ]

    return payload


@router.patch(
    "/shifts/{shift_id}",
    response_model=ShiftResponse,
)
async def update_shift(
    shift_id: uuid.UUID,
    request: ShiftUpdateRequest,
    scope: TenantScope,
):
    permission_service(
        scope
    ).require(
        WorkspacePermission
        .SHIFTS_MANAGE
        .value
    )

    return await ShiftService(
        scope.session
    ).update_shift(
        shift_id=shift_id,
        request=request,
    )


@router.delete(
    "/shifts/{shift_id}",
    status_code=(
        status.HTTP_204_NO_CONTENT
    ),
)
async def deactivate_shift(
    shift_id: uuid.UUID,
    scope: TenantScope,
):
    permission_service(
        scope
    ).require(
        WorkspacePermission
        .SHIFTS_MANAGE
        .value
    )

    await ShiftService(
        scope.session
    ).deactivate_shift(
        shift_id=shift_id
    )

    return Response(
        status_code=(
            status.HTTP_204_NO_CONTENT
        )
    )


# =========================================================
# ASSIGNMENTS
# =========================================================


@router.get(
    "/shift-assignments",
    response_model=list[
        ShiftAssignmentResponse
    ],
)
async def list_shift_assignments(
    scope: TenantScope,
    target_type: (
        ShiftAssignmentTargetType
        | None
    ) = Query(
        default=None
    ),
    target_id: (
        uuid.UUID | None
    ) = Query(
        default=None
    ),
):
    permissions = (
        permission_service(
            scope
        )
    )

    access = (
        access_service(
            scope
        )
    )

    # -----------------------------------------------------
    # ALL SCOPE
    # -----------------------------------------------------

    if permissions.has(
        WorkspacePermission
        .SHIFTS_ALL_READ
        .value
    ):
        return await ShiftService(
            scope.session
        ).list_assignments(
            target_type=target_type,
            target_id=target_id,
        )

    # -----------------------------------------------------
    # SCOPED ACCESS
    # -----------------------------------------------------

    permissions.require_any(
        {
            WorkspacePermission
            .SHIFTS_SELF_READ
            .value,

            WorkspacePermission
            .SHIFTS_TEAM_READ
            .value,
        }
    )

    if (
        target_type is None
        or target_id is None
    ):
        raise HTTPException(
            status_code=(
                status
                .HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=(
                "target_type and target_id "
                "are required for scoped "
                "assignment reads."
            ),
        )

    # -----------------------------------------------------
    # EMPLOYEE TARGET
    # -----------------------------------------------------

    if (
        target_type
        == (
            ShiftAssignmentTargetType
            .EMPLOYEE
        )
    ):
        await access.require_schedule_read(
            employee_id=target_id
        )

    # -----------------------------------------------------
    # TEAM TARGET
    # -----------------------------------------------------

    elif (
        target_type
        == (
            ShiftAssignmentTargetType
            .TEAM
        )
    ):
        await (
            access
            .require_team_schedule_read(
                team_id=target_id
            )
        )

    else:
        raise HTTPException(
            status_code=(
                status
                .HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=(
                "Unsupported assignment "
                "target type."
            ),
        )

    return await ShiftService(
        scope.session
    ).list_assignments(
        target_type=target_type,
        target_id=target_id,
    )


@router.post(
    "/shift-assignments",
    response_model=(
        ShiftAssignmentResponse
    ),
    status_code=(
        status.HTTP_201_CREATED
    ),
)
async def create_shift_assignment(
    request: (
        ShiftAssignmentCreateRequest
    ),
    scope: TenantScope,
):
    permission_service(
        scope
    ).require(
        WorkspacePermission
        .SHIFTS_MANAGE
        .value
    )

    return await ShiftService(
        scope.session
    ).create_assignment(
        request
    )


@router.patch(
    "/shift-assignments/"
    "{assignment_id}",
    response_model=(
        ShiftAssignmentResponse
    ),
)
async def update_shift_assignment(
    assignment_id: uuid.UUID,
    request: (
        ShiftAssignmentUpdateRequest
    ),
    scope: TenantScope,
):
    permission_service(
        scope
    ).require(
        WorkspacePermission
        .SHIFTS_MANAGE
        .value
    )

    return await ShiftService(
        scope.session
    ).update_assignment(
        assignment_id=(
            assignment_id
        ),
        request=request,
    )


@router.delete(
    "/shift-assignments/"
    "{assignment_id}",
    status_code=(
        status.HTTP_204_NO_CONTENT
    ),
)
async def delete_shift_assignment(
    assignment_id: uuid.UUID,
    scope: TenantScope,
):
    permission_service(
        scope
    ).require(
        WorkspacePermission
        .SHIFTS_MANAGE
        .value
    )

    await ShiftService(
        scope.session
    ).delete_assignment(
        assignment_id=(
            assignment_id
        )
    )

    return Response(
        status_code=(
            status.HTTP_204_NO_CONTENT
        )
    )


# =========================================================
# EXCEPTIONS
# =========================================================


@router.get(
    "/schedule-exceptions",
    response_model=list[
        ScheduleExceptionResponse
    ],
)
async def list_schedule_exceptions(
    scope: TenantScope,
    employee_id: (
        uuid.UUID | None
    ) = Query(
        default=None
    ),
    start_date: (
        date | None
    ) = Query(
        default=None
    ),
    end_date: (
        date | None
    ) = Query(
        default=None
    ),
):
    permissions = (
        permission_service(
            scope
        )
    )

    # -----------------------------------------------------
    # ALL SCOPE
    # -----------------------------------------------------

    if permissions.has(
        WorkspacePermission
        .SHIFTS_ALL_READ
        .value
    ):
        return await (
            ShiftService(
                scope.session
            )
            .repository
            .list_exceptions(
                employee_id=employee_id,
                start_date=start_date,
                end_date=end_date,
            )
        )

    # -----------------------------------------------------
    # SELF / TEAM SCOPE
    # -----------------------------------------------------

    permissions.require_any(
        {
            WorkspacePermission
            .SHIFTS_SELF_READ
            .value,

            WorkspacePermission
            .SHIFTS_TEAM_READ
            .value,
        }
    )

    if employee_id is None:
        raise HTTPException(
            status_code=(
                status
                .HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=(
                "employee_id is required "
                "for scoped exception reads."
            ),
        )

    await access_service(
        scope
    ).require_schedule_read(
        employee_id=employee_id
    )

    return await (
        ShiftService(
            scope.session
        )
        .repository
        .list_exceptions(
            employee_id=employee_id,
            start_date=start_date,
            end_date=end_date,
        )
    )


@router.post(
    "/schedule-exceptions",
    response_model=(
        ScheduleExceptionResponse
    ),
    status_code=(
        status.HTTP_201_CREATED
    ),
)
async def create_schedule_exception(
    request: (
        ScheduleExceptionCreateRequest
    ),
    scope: TenantScope,
):
    permission_service(
        scope
    ).require(
        WorkspacePermission
        .SHIFTS_MANAGE
        .value
    )

    return await ShiftService(
        scope.session
    ).create_exception(
        actor_user_id=(
            scope.user_id
        ),
        request=request,
    )


@router.patch(
    "/schedule-exceptions/"
    "{exception_id}",
    response_model=(
        ScheduleExceptionResponse
    ),
)
async def update_schedule_exception(
    exception_id: uuid.UUID,
    request: (
        ScheduleExceptionUpdateRequest
    ),
    scope: TenantScope,
):
    permission_service(
        scope
    ).require(
        WorkspacePermission
        .SHIFTS_MANAGE
        .value
    )

    return await ShiftService(
        scope.session
    ).update_exception(
        exception_id=exception_id,
        request=request,
    )


@router.delete(
    "/schedule-exceptions/"
    "{exception_id}",
    status_code=(
        status.HTTP_204_NO_CONTENT
    ),
)
async def delete_schedule_exception(
    exception_id: uuid.UUID,
    scope: TenantScope,
):
    permission_service(
        scope
    ).require(
        WorkspacePermission
        .SHIFTS_MANAGE
        .value
    )

    await ShiftService(
        scope.session
    ).delete_exception(
        exception_id=exception_id
    )

    return Response(
        status_code=(
            status.HTTP_204_NO_CONTENT
        )
    )


# =========================================================
# PUBLICATION
# =========================================================


@router.get(
    "/schedules/publications",
    response_model=list[
        SchedulePublicationResponse
    ],
)
async def list_schedule_publications(
    scope: TenantScope,
):
    permission_service(
        scope
    ).require_any(
        {
            WorkspacePermission
            .SHIFTS_VIEW
            .value,

            WorkspacePermission
            .SHIFTS_ALL_READ
            .value,
        }
    )

    return await (
        ShiftService(
            scope.session
        )
        .repository
        .list_publications()
    )


@router.post(
    "/schedules/publish",
    response_model=(
        SchedulePublicationResponse
    ),
    status_code=(
        status.HTTP_201_CREATED
    ),
)
async def publish_schedule(
    request: SchedulePublishRequest,
    scope: TenantScope,
    control_session: ControlDB,
):
    """
    Publish an immutable employee/day schedule snapshot.

    Flow:

        permission
            ↓
        tenant publication + snapshots
            ↓
        tenant commit
            ↓
        control-plane audit append

    The control audit database and tenant database are separate
    PostgreSQL databases and therefore cannot share one SQL
    transaction.
    """

    permission_service(
        scope
    ).require(
        WorkspacePermission
        .SHIFTS_MANAGE
        .value
    )

    publication = await (
        SchedulePublicationSnapshotService(
            scope.session
        )
        .publish(
            actor_user_id=(
                scope.user_id
            ),
            request=request,
        )
    )

    await audit_schedule_published(
        control_session=(
            control_session
        ),
        workspace_id=(
            scope.workspace_id
        ),
        actor_user_id=(
            scope.user_id
        ),
        publication=publication,
    )

    return publication


# =========================================================
# MY SCHEDULE
# =========================================================


@router.get(
    "/schedules/me",
    response_model=list[
        ResolvedScheduleDayResponse
    ],
)
async def resolved_my_schedule(
    scope: TenantScope,
    start_date: date = Query(
        ...
    ),
    end_date: date = Query(
        ...
    ),
):
    validate_schedule_range(
        start_date=start_date,
        end_date=end_date,
    )

    employee = await (
        access_service(
            scope
        )
        .require_self_employee()
    )

    return await resolve_schedule_range(
        service=ShiftService(
            scope.session
        ),
        employee_id=employee.id,
        start_date=start_date,
        end_date=end_date,
    )


# =========================================================
# RESOLVED EMPLOYEE SCHEDULE
# =========================================================


@router.get(
    "/schedules/employees/"
    "{employee_id}",
    response_model=list[
        ResolvedScheduleDayResponse
    ],
)
async def resolved_employee_schedule(
    employee_id: uuid.UUID,
    scope: TenantScope,
    start_date: date = Query(
        ...
    ),
    end_date: date = Query(
        ...
    ),
):
    validate_schedule_range(
        start_date=start_date,
        end_date=end_date,
    )

    await access_service(
        scope
    ).require_schedule_read(
        employee_id=employee_id
    )

    return await resolve_schedule_range(
        service=ShiftService(
            scope.session
        ),
        employee_id=employee_id,
        start_date=start_date,
        end_date=end_date,
    )


__all__ = [
    "router",
]