from __future__ import annotations

import uuid

from fastapi import (
    APIRouter,
    HTTPException,
    status,
)

from app.db.tenant_dependency import TenantScope
from app.modules.employee_lifecycle.schemas import (
    OffboardingCreateRequest,
    OffboardingResponse,
    OffboardingUpdateRequest,
    OnboardingCreateRequest,
    OnboardingResponse,
    OnboardingUpdateRequest,
)
from app.modules.employee_lifecycle.service import (
    EmployeeLifecycleService,
)
from app.modules.workspaces.models import (
    WORKSPACE_ROLE_ADMIN,
    WORKSPACE_ROLE_OWNER,
)


router = APIRouter(
    prefix="/workspaces/{workspace_id}/employee-lifecycle",
    tags=["Employee Lifecycle"],
)


def service(
    scope: TenantScope,
) -> EmployeeLifecycleService:
    return EmployeeLifecycleService(scope.session)


def require_manager(
    scope: TenantScope,
) -> None:
    if scope.role_key not in {
        WORKSPACE_ROLE_OWNER,
        WORKSPACE_ROLE_ADMIN,
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Workspace OWNER or ADMIN role required.",
        )


@router.post(
    "/onboarding",
    response_model=OnboardingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_onboarding(
    request: OnboardingCreateRequest,
    scope: TenantScope,
) -> OnboardingResponse:
    require_manager(scope)
    return await service(scope).create_onboarding(request)


@router.patch(
    "/onboarding/{record_id}",
    response_model=OnboardingResponse,
)
async def update_onboarding(
    record_id: uuid.UUID,
    request: OnboardingUpdateRequest,
    scope: TenantScope,
) -> OnboardingResponse:
    require_manager(scope)
    return await service(scope).update_onboarding(
        record_id,
        request,
    )


@router.post(
    "/offboarding",
    response_model=OffboardingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_offboarding(
    request: OffboardingCreateRequest,
    scope: TenantScope,
) -> OffboardingResponse:
    require_manager(scope)
    return await service(scope).create_offboarding(request)


@router.patch(
    "/offboarding/{record_id}",
    response_model=OffboardingResponse,
)
async def update_offboarding(
    record_id: uuid.UUID,
    request: OffboardingUpdateRequest,
    scope: TenantScope,
) -> OffboardingResponse:
    require_manager(scope)
    return await service(scope).update_offboarding(
        record_id,
        request,
    )


__all__ = ["router"]