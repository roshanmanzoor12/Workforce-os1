from __future__ import annotations

import uuid
from datetime import date

from fastapi import (
    APIRouter,
    Query,
    Response,
    status,
)

from app.db.tenant_dependency import (
    TenantScope,
)
from app.modules.holidays.schemas import (
    HolidayCreateRequest,
    HolidayResponse,
    HolidayUpdateRequest,
)
from app.modules.holidays.service import (
    HolidayService,
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
        "/holidays"
    ),
    tags=["Holidays"],
)


def permission_service(
    scope: TenantScope,
) -> WorkspacePermissionService:
    return WorkspacePermissionService(
        scope
    )


# =========================================================
# LIST HOLIDAYS
# =========================================================


@router.get(
    "",
    response_model=list[
        HolidayResponse
    ],
)
async def list_holidays(
    scope: TenantScope,
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
    active_only: bool = Query(
        default=False
    ),
):
    permission_service(
        scope
    ).require_any(
        {
            WorkspacePermission
            .HOLIDAYS_VIEW
            .value,

            WorkspacePermission
            .HOLIDAYS_SELF_READ
            .value,

            WorkspacePermission
            .HOLIDAYS_TEAM_READ
            .value,

            WorkspacePermission
            .HOLIDAYS_ALL_READ
            .value,
        }
    )

    return await HolidayService(
        scope.session
    ).list_holidays(
        start_date=start_date,
        end_date=end_date,
        active_only=active_only,
    )


# =========================================================
# CREATE HOLIDAY
# =========================================================


@router.post(
    "",
    response_model=HolidayResponse,
    status_code=(
        status.HTTP_201_CREATED
    ),
)
async def create_holiday(
    request: HolidayCreateRequest,
    scope: TenantScope,
):
    permission_service(
        scope
    ).require(
        WorkspacePermission
        .HOLIDAYS_MANAGE
        .value
    )

    return await HolidayService(
        scope.session
    ).create_holiday(
        actor_user_id=(
            scope.user_id
        ),
        request=request,
    )


# =========================================================
# GET HOLIDAY
# =========================================================


@router.get(
    "/{holiday_id}",
    response_model=HolidayResponse,
)
async def get_holiday(
    holiday_id: uuid.UUID,
    scope: TenantScope,
):
    permission_service(
        scope
    ).require_any(
        {
            WorkspacePermission
            .HOLIDAYS_VIEW
            .value,

            WorkspacePermission
            .HOLIDAYS_SELF_READ
            .value,

            WorkspacePermission
            .HOLIDAYS_TEAM_READ
            .value,

            WorkspacePermission
            .HOLIDAYS_ALL_READ
            .value,
        }
    )

    return await HolidayService(
        scope.session
    ).get_holiday(
        holiday_id=holiday_id
    )


# =========================================================
# UPDATE HOLIDAY
# =========================================================


@router.patch(
    "/{holiday_id}",
    response_model=HolidayResponse,
)
async def update_holiday(
    holiday_id: uuid.UUID,
    request: HolidayUpdateRequest,
    scope: TenantScope,
):
    permission_service(
        scope
    ).require(
        WorkspacePermission
        .HOLIDAYS_MANAGE
        .value
    )

    return await HolidayService(
        scope.session
    ).update_holiday(
        holiday_id=holiday_id,
        request=request,
    )


# =========================================================
# DEACTIVATE HOLIDAY
# =========================================================


@router.delete(
    "/{holiday_id}",
    status_code=(
        status.HTTP_204_NO_CONTENT
    ),
)
async def deactivate_holiday(
    holiday_id: uuid.UUID,
    scope: TenantScope,
):
    permission_service(
        scope
    ).require(
        WorkspacePermission
        .HOLIDAYS_MANAGE
        .value
    )

    await HolidayService(
        scope.session
    ).deactivate_holiday(
        holiday_id=holiday_id
    )

    return Response(
        status_code=(
            status.HTTP_204_NO_CONTENT
        )
    )


__all__ = [
    "router",
]