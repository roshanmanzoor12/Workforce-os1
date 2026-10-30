from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.modules.platform_admin.permissions import (
    require_platform_admin,
)
from app.modules.platform_admin.schemas import (
    PlatformSummaryResponse,
    PlatformTenantListResponse,
    PlatformTenantPublic,
    PlatformTenantStatusUpdate,
)
from app.modules.platform_admin.service import (
    PlatformAdminService,
    PlatformTenantNotFoundError,
    PlatformTenantValidationError,
)


router = APIRouter(
    prefix="/platform-admin",
    tags=["platform-admin"],
)

_service = PlatformAdminService()


@router.get(
    "/tenants",
    response_model=PlatformTenantListResponse,
)
async def list_platform_tenants() -> PlatformTenantListResponse:
    require_platform_admin()

    tenants = await _service.list_tenants()

    return PlatformTenantListResponse(
        items=[
            PlatformTenantPublic.model_validate(tenant)
            for tenant in tenants
        ],
        total=len(tenants),
    )


@router.get(
    "/tenants/{tenant_id}",
    response_model=PlatformTenantPublic,
)
async def get_platform_tenant(
    tenant_id: UUID,
) -> PlatformTenantPublic:
    require_platform_admin()

    try:
        tenant = await _service.get_tenant(tenant_id)
    except PlatformTenantNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return PlatformTenantPublic.model_validate(tenant)


@router.patch(
    "/tenants/{tenant_id}/status",
    response_model=PlatformTenantPublic,
)
async def update_platform_tenant_status(
    tenant_id: UUID,
    request: PlatformTenantStatusUpdate,
) -> PlatformTenantPublic:
    require_platform_admin()

    try:
        tenant = await _service.update_status(
            tenant_id=tenant_id,
            status=request.status,
        )
    except PlatformTenantNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except PlatformTenantValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return PlatformTenantPublic.model_validate(tenant)


@router.get(
    "/summary",
    response_model=PlatformSummaryResponse,
)
async def get_platform_summary() -> PlatformSummaryResponse:
    require_platform_admin()

    summary = await _service.summary()

    return PlatformSummaryResponse(
        tenant_count=summary.tenant_count,
        active_tenant_count=summary.active_tenant_count,
        suspended_tenant_count=summary.suspended_tenant_count,
        plan_counts=summary.plan_counts,
        generated_at=summary.generated_at,
    )