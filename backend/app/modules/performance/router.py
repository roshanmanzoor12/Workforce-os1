from __future__ import annotations

import uuid

from fastapi import (
    APIRouter,
    status,
)

from app.db.tenant_dependency import TenantScope
from app.modules.performance.schemas import (
    CyclePublic,
    ReviewCreate,
    ReviewCycleCreate,
    ReviewList,
    ReviewPublic,
)
from app.modules.performance.service import (
    PerformanceService,
)


router = APIRouter(
    prefix=(
        "/workspaces/"
        "{workspace_id}/performance"
    ),
    tags=["performance"],
)


def performance_service(
    scope: TenantScope,
) -> PerformanceService:
    return PerformanceService(
        scope.session,
        scope.user_id,
    )


@router.post(
    "/cycles",
    response_model=CyclePublic,
    status_code=status.HTTP_201_CREATED,
)
async def create_review_cycle(
    request: ReviewCycleCreate,
    scope: TenantScope,
) -> CyclePublic:
    return await performance_service(
        scope
    ).create_cycle(request)


@router.post(
    "/reviews",
    response_model=ReviewPublic,
    status_code=status.HTTP_201_CREATED,
)
async def create_performance_review(
    request: ReviewCreate,
    scope: TenantScope,
) -> ReviewPublic:
    return await performance_service(
        scope
    ).create_review(request)


@router.get(
    "/reviews",
    response_model=ReviewList,
)
async def list_performance_reviews(
    scope: TenantScope,
    employee_id: uuid.UUID | None = None,
) -> ReviewList:
    return await performance_service(
        scope
    ).list_reviews(employee_id)


__all__ = [
    "router",
]