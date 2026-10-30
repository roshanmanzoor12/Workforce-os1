from __future__ import annotations

import uuid
from typing import (
    Annotated,
    Any,
)

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)

from app.core.exceptions import (
    ValidationError,
)
from app.modules.tenant_api.dependencies import (
    get_authorized_tenant_context,
)
from app.modules.workforce_intelligence.access import (
    resolve_intelligence_access,
)
from app.modules.workforce_intelligence.schemas import (
    EmployeeIntelligenceResponse,
    IntelligenceCapabilitiesResponse,
    WorkforceOverview,
    WorkforceSignalResponse,
    WorkforceTrendResponse,
)
from app.modules.workforce_intelligence.service import (
    WorkforceIntelligenceService,
)


router = APIRouter(
    prefix=(
        "/workspaces/"
        "{workspace_id}/workforce-intelligence"
    ),
    tags=[
        "workforce-intelligence",
    ],
)


TenantContext = Annotated[
    Any,
    Depends(
        get_authorized_tenant_context
    ),
]


async def _access(
    *,
    workspace_id: uuid.UUID,
    context: Any,
):
    try:
        return await (
            resolve_intelligence_access(
                workspace_id=workspace_id,
                context=context,
            )
        )

    except ValidationError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=str(
                exc
            ),
        ) from exc


def _service(
    context: Any,
) -> WorkforceIntelligenceService:
    return (
        WorkforceIntelligenceService(
            context.tenant_session
        )
    )


@router.get(
    "/overview",
    response_model=WorkforceOverview,
)
async def intelligence_overview(
    workspace_id: uuid.UUID,
    context: TenantContext,

    days: int = Query(
        default=30,
        ge=1,
        le=366,
    ),
) -> WorkforceOverview:
    access = await _access(
        workspace_id=workspace_id,
        context=context,
    )

    try:
        return await (
            _service(
                context
            )
            .overview(
                access=access,
                days=days,
            )
        )

    except ValidationError as exc:
        raise HTTPException(
            status_code=(
                status
                .HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=str(
                exc
            ),
        ) from exc


@router.get(
    "/employees",
    response_model=(
        EmployeeIntelligenceResponse
    ),
)
async def intelligence_employees(
    workspace_id: uuid.UUID,
    context: TenantContext,

    days: int = Query(
        default=30,
        ge=1,
        le=366,
    ),

    limit: int = Query(
        default=100,
        ge=1,
        le=500,
    ),
) -> EmployeeIntelligenceResponse:
    access = await _access(
        workspace_id=workspace_id,
        context=context,
    )

    return await (
        _service(
            context
        )
        .employees(
            access=access,
            days=days,
            limit=limit,
        )
    )


@router.get(
    "/trends",
    response_model=(
        WorkforceTrendResponse
    ),
)
async def intelligence_trends(
    workspace_id: uuid.UUID,
    context: TenantContext,

    days: int = Query(
        default=30,
        ge=1,
        le=366,
    ),
) -> WorkforceTrendResponse:
    access = await _access(
        workspace_id=workspace_id,
        context=context,
    )

    return await (
        _service(
            context
        )
        .trends(
            access=access,
            days=days,
        )
    )


@router.get(
    "/signals",
    response_model=(
        WorkforceSignalResponse
    ),
)
async def intelligence_signals(
    workspace_id: uuid.UUID,
    context: TenantContext,

    days: int = Query(
        default=30,
        ge=1,
        le=366,
    ),
) -> WorkforceSignalResponse:
    access = await _access(
        workspace_id=workspace_id,
        context=context,
    )

    return await (
        _service(
            context
        )
        .signals(
            access=access,
            days=days,
        )
    )


@router.get(
    "/capabilities",
    response_model=(
        IntelligenceCapabilitiesResponse
    ),
)
async def intelligence_capabilities(
    workspace_id: uuid.UUID,
    context: TenantContext,
) -> IntelligenceCapabilitiesResponse:
    access = await _access(
        workspace_id=workspace_id,
        context=context,
    )

    return (
        WorkforceIntelligenceService
        .capabilities(
            access=access
        )
    )


__all__ = [
    "router",
]