from __future__ import annotations

import uuid
from datetime import datetime
from typing import (
    Annotated,
    Any,
)

from fastapi import (
    APIRouter,
    Depends,
    Query,
)

from app.modules.productivity_insights.access import (
    resolve_productivity_insights_access,
)
from app.modules.productivity_insights.schemas import (
    ProductivityActivityResponse,
    ProductivityComparisonResponse,
    ProductivityGoalsResponse,
    ProductivityOverviewResponse,
    ProductivityUsageResponse,
)
from app.modules.productivity_insights.service import (
    ProductivityInsightsService,
)
from app.modules.tenant_api.dependencies import (
    get_authorized_tenant_context,
)


router = APIRouter(
    prefix=(
        "/workspaces/"
        "{workspace_id}/productivity-insights"
    ),
    tags=[
        "productivity-insights",
    ],
)


TenantContext = Annotated[
    Any,
    Depends(
        get_authorized_tenant_context
    ),
]


def _service(
    context: Any,
) -> ProductivityInsightsService:
    return ProductivityInsightsService(
        context.tenant_session
    )


async def _access(
    *,
    workspace_id: uuid.UUID,
    context: Any,
):
    return await (
        resolve_productivity_insights_access(
            workspace_id=workspace_id,
            context=context,
        )
    )


def _window(
    *,
    start_at: datetime | None,
    end_at: datetime | None,
):
    return (
        ProductivityInsightsService
        .resolve_window(
            start_at=start_at,
            end_at=end_at,
        )
    )


@router.get(
    "/overview",
    response_model=(
        ProductivityOverviewResponse
    ),
)
async def productivity_overview(
    workspace_id: uuid.UUID,
    context: TenantContext,
    start_at: datetime | None = Query(
        default=None,
    ),
    end_at: datetime | None = Query(
        default=None,
    ),
) -> ProductivityOverviewResponse:
    access = await _access(
        workspace_id=workspace_id,
        context=context,
    )

    return await (
        _service(
            context
        )
        .overview(
            workspace_id=workspace_id,
            access=access,
            window=_window(
                start_at=start_at,
                end_at=end_at,
            ),
        )
    )


@router.get(
    "/activity",
    response_model=(
        ProductivityActivityResponse
    ),
)
async def productivity_activity(
    workspace_id: uuid.UUID,
    context: TenantContext,
    start_at: datetime | None = Query(
        default=None,
    ),
    end_at: datetime | None = Query(
        default=None,
    ),
) -> ProductivityActivityResponse:
    access = await _access(
        workspace_id=workspace_id,
        context=context,
    )

    return await (
        _service(
            context
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
    "/usage",
    response_model=(
        ProductivityUsageResponse
    ),
)
async def productivity_usage(
    workspace_id: uuid.UUID,
    context: TenantContext,
    start_at: datetime | None = Query(
        default=None,
    ),
    end_at: datetime | None = Query(
        default=None,
    ),
) -> ProductivityUsageResponse:
    access = await _access(
        workspace_id=workspace_id,
        context=context,
    )

    return await (
        _service(
            context
        )
        .usage(
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
        ProductivityGoalsResponse
    ),
)
async def productivity_goals(
    workspace_id: uuid.UUID,
    context: TenantContext,
    start_at: datetime | None = Query(
        default=None,
    ),
    end_at: datetime | None = Query(
        default=None,
    ),
) -> ProductivityGoalsResponse:
    access = await _access(
        workspace_id=workspace_id,
        context=context,
    )

    return await (
        _service(
            context
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
    "/comparison",
    response_model=(
        ProductivityComparisonResponse
    ),
)
async def productivity_comparison(
    workspace_id: uuid.UUID,
    context: TenantContext,
    start_at: datetime | None = Query(
        default=None,
    ),
    end_at: datetime | None = Query(
        default=None,
    ),
) -> ProductivityComparisonResponse:
    access = await _access(
        workspace_id=workspace_id,
        context=context,
    )

    return await (
        _service(
            context
        )
        .comparison(
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