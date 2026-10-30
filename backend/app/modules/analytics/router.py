from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import (
    APIRouter,
    Depends,
    Query,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.core.database import (
    get_control_db,
)
from app.db.tenant_dependency import (
    TenantScope,
)
from app.modules.analytics.access import (
    resolve_analytics_access,
)
from app.modules.analytics.schemas import (
    AnalyticsActivityResponse,
    AnalyticsAppsResponse,
    AnalyticsAttendanceResponse,
    AnalyticsGoalsResponse,
    AnalyticsOverviewResponse,
    AnalyticsProductivityResponse,
    AnalyticsTrendsResponse,
    AnalyticsWebsitesResponse,
)
from app.modules.analytics.service import (
    AnalyticsService,
)
from app.modules.auth.models import User
from app.modules.auth.permissions import (
    get_current_verified_user,
)


router = APIRouter(
    prefix=(
        "/workspaces/"
        "{workspace_id}/analytics"
    ),
    tags=[
        "Analytics",
    ],
)


async def _access(
    *,
    workspace_id: uuid.UUID,
    scope: TenantScope,
    control_session: AsyncSession,
    current_user: User,
):
    return await (
        resolve_analytics_access(
            workspace_id=workspace_id,
            scope=scope,
            control_session=(
                control_session
            ),
            current_user=current_user,
        )
    )


def _window(
    *,
    start_at: datetime | None,
    end_at: datetime | None,
):
    return (
        AnalyticsService
        .resolve_window(
            start_at=start_at,
            end_at=end_at,
        )
    )


@router.get(
    "/overview",
    response_model=(
        AnalyticsOverviewResponse
    ),
)
async def analytics_overview(
    workspace_id: uuid.UUID,
    scope: TenantScope,
    control_session: AsyncSession = Depends(
        get_control_db
    ),
    current_user: User = Depends(
        get_current_verified_user
    ),
    start_at: datetime | None = Query(
        default=None
    ),
    end_at: datetime | None = Query(
        default=None
    ),
) -> AnalyticsOverviewResponse:
    access = await _access(
        workspace_id=workspace_id,
        scope=scope,
        control_session=(
            control_session
        ),
        current_user=current_user,
    )

    service = AnalyticsService(
        scope.session
    )

    return await service.overview(
        workspace_id=workspace_id,
        access=access,
        window=_window(
            start_at=start_at,
            end_at=end_at,
        ),
    )


@router.get(
    "/activity",
    response_model=(
        AnalyticsActivityResponse
    ),
)
async def analytics_activity(
    workspace_id: uuid.UUID,
    scope: TenantScope,
    control_session: AsyncSession = Depends(
        get_control_db
    ),
    current_user: User = Depends(
        get_current_verified_user
    ),
    start_at: datetime | None = Query(
        default=None
    ),
    end_at: datetime | None = Query(
        default=None
    ),
) -> AnalyticsActivityResponse:
    access = await _access(
        workspace_id=workspace_id,
        scope=scope,
        control_session=(
            control_session
        ),
        current_user=current_user,
    )

    return await (
        AnalyticsService(
            scope.session
        )
        .activity(
            workspace_id=workspace_id,
            access=access,
            window=_window(
                start_at=start_at,
                end_at=end_at,
            ),
        )
    )


@router.get(
    "/attendance",
    response_model=(
        AnalyticsAttendanceResponse
    ),
)
async def analytics_attendance(
    workspace_id: uuid.UUID,
    scope: TenantScope,
    control_session: AsyncSession = Depends(
        get_control_db
    ),
    current_user: User = Depends(
        get_current_verified_user
    ),
    start_at: datetime | None = Query(
        default=None
    ),
    end_at: datetime | None = Query(
        default=None
    ),
) -> AnalyticsAttendanceResponse:
    access = await _access(
        workspace_id=workspace_id,
        scope=scope,
        control_session=(
            control_session
        ),
        current_user=current_user,
    )

    return await (
        AnalyticsService(
            scope.session
        )
        .attendance(
            workspace_id=workspace_id,
            access=access,
            window=_window(
                start_at=start_at,
                end_at=end_at,
            ),
        )
    )


@router.get(
    "/productivity",
    response_model=(
        AnalyticsProductivityResponse
    ),
)
async def analytics_productivity(
    workspace_id: uuid.UUID,
    scope: TenantScope,
    control_session: AsyncSession = Depends(
        get_control_db
    ),
    current_user: User = Depends(
        get_current_verified_user
    ),
    start_at: datetime | None = Query(
        default=None
    ),
    end_at: datetime | None = Query(
        default=None
    ),
) -> AnalyticsProductivityResponse:
    access = await _access(
        workspace_id=workspace_id,
        scope=scope,
        control_session=(
            control_session
        ),
        current_user=current_user,
    )

    return await (
        AnalyticsService(
            scope.session
        )
        .productivity(
            workspace_id=workspace_id,
            access=access,
            window=_window(
                start_at=start_at,
                end_at=end_at,
            ),
        )
    )


@router.get(
    "/apps",
    response_model=(
        AnalyticsAppsResponse
    ),
)
async def analytics_apps(
    workspace_id: uuid.UUID,
    scope: TenantScope,
    control_session: AsyncSession = Depends(
        get_control_db
    ),
    current_user: User = Depends(
        get_current_verified_user
    ),
    start_at: datetime | None = Query(
        default=None
    ),
    end_at: datetime | None = Query(
        default=None
    ),
) -> AnalyticsAppsResponse:
    access = await _access(
        workspace_id=workspace_id,
        scope=scope,
        control_session=(
            control_session
        ),
        current_user=current_user,
    )

    return await (
        AnalyticsService(
            scope.session
        )
        .apps(
            workspace_id=workspace_id,
            access=access,
            window=_window(
                start_at=start_at,
                end_at=end_at,
            ),
        )
    )


@router.get(
    "/websites",
    response_model=(
        AnalyticsWebsitesResponse
    ),
)
async def analytics_websites(
    workspace_id: uuid.UUID,
    scope: TenantScope,
    control_session: AsyncSession = Depends(
        get_control_db
    ),
    current_user: User = Depends(
        get_current_verified_user
    ),
    start_at: datetime | None = Query(
        default=None
    ),
    end_at: datetime | None = Query(
        default=None
    ),
) -> AnalyticsWebsitesResponse:
    access = await _access(
        workspace_id=workspace_id,
        scope=scope,
        control_session=(
            control_session
        ),
        current_user=current_user,
    )

    return await (
        AnalyticsService(
            scope.session
        )
        .websites(
            workspace_id=workspace_id,
            access=access,
            window=_window(
                start_at=start_at,
                end_at=end_at,
            ),
        )
    )


@router.get(
    "/goals",
    response_model=(
        AnalyticsGoalsResponse
    ),
)
async def analytics_goals(
    workspace_id: uuid.UUID,
    scope: TenantScope,
    control_session: AsyncSession = Depends(
        get_control_db
    ),
    current_user: User = Depends(
        get_current_verified_user
    ),
    start_at: datetime | None = Query(
        default=None
    ),
    end_at: datetime | None = Query(
        default=None
    ),
) -> AnalyticsGoalsResponse:
    access = await _access(
        workspace_id=workspace_id,
        scope=scope,
        control_session=(
            control_session
        ),
        current_user=current_user,
    )

    return await (
        AnalyticsService(
            scope.session
        )
        .goals(
            workspace_id=workspace_id,
            access=access,
            window=_window(
                start_at=start_at,
                end_at=end_at,
            ),
        )
    )


@router.get(
    "/trends",
    response_model=(
        AnalyticsTrendsResponse
    ),
)
async def analytics_trends(
    workspace_id: uuid.UUID,
    scope: TenantScope,
    control_session: AsyncSession = Depends(
        get_control_db
    ),
    current_user: User = Depends(
        get_current_verified_user
    ),
    start_at: datetime | None = Query(
        default=None
    ),
    end_at: datetime | None = Query(
        default=None
    ),
) -> AnalyticsTrendsResponse:
    access = await _access(
        workspace_id=workspace_id,
        scope=scope,
        control_session=(
            control_session
        ),
        current_user=current_user,
    )

    return await (
        AnalyticsService(
            scope.session
        )
        .trends(
            workspace_id=workspace_id,
            access=access,
            window=_window(
                start_at=start_at,
                end_at=end_at,
            ),
        )
    )


__all__ = [
    "router",
]