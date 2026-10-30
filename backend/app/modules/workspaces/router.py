from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Request,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_control_db
from app.middleware.request_id import get_request_id
from app.modules.auth.models import User
from app.modules.auth.permissions import get_current_verified_user
from app.modules.workspaces.provisioning_schemas import (
    WorkspaceProvisioningResponse,
    WorkspaceProvisioningRetryResponse,
)

from app.modules.workspaces.bootstrap_schemas import (
    WorkspaceBootstrapResponse,
)
from app.modules.workspaces.bootstrap_service import (
    WorkspaceBootstrapService,
)

from app.modules.workspaces.schemas import (
    WorkspaceCreateRequest,
    WorkspaceCreateResponse,
    WorkspaceDetailResponse,
    WorkspaceListResponse,
    WorkspaceMembershipRemoveResponse,
    WorkspaceMembershipResponse,
    WorkspaceMembershipRoleUpdateRequest,
    WorkspaceMembershipStatusUpdateRequest,
    WorkspaceStateResponse,
    WorkspaceUpdateRequest,
)
from app.modules.workspaces.service import WorkspaceService


router = APIRouter(
    prefix="/workspaces",
    tags=["Workspaces"],
)


# =========================================================
# DEPENDENCIES
# =========================================================


ControlDB = Annotated[
    AsyncSession,
    Depends(get_control_db),
]


VerifiedUser = Annotated[
    User,
    Depends(get_current_verified_user),
]


def get_workspace_service(
    db: ControlDB,
) -> WorkspaceService:
    return WorkspaceService(
        db
    )


WorkspaceServiceDependency = Annotated[
    WorkspaceService,
    Depends(get_workspace_service),
]

def get_workspace_bootstrap_service(
    db: ControlDB,
) -> WorkspaceBootstrapService:
    return WorkspaceBootstrapService(
        WorkspaceService(db)
    )


WorkspaceBootstrapServiceDependency = Annotated[
    WorkspaceBootstrapService,
    Depends(get_workspace_bootstrap_service),
]

# =========================================================
# REQUEST METADATA
# =========================================================


def get_request_context_id(
    request: Request,
) -> str | None:
    return get_request_id(
        request
    )


# =========================================================
# CREATE WORKSPACE
# =========================================================


@router.post(
    "",
    response_model=WorkspaceCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a workspace",
)
async def create_workspace(
    payload: WorkspaceCreateRequest,
    workspace_service: WorkspaceServiceDependency,
    current_user: VerifiedUser,
) -> WorkspaceCreateResponse:
    return await workspace_service.create_workspace(
        payload,
        user=current_user,
    )


# =========================================================
# LIST CURRENT USER WORKSPACES
# =========================================================


@router.get(
    "",
    response_model=WorkspaceListResponse,
    status_code=status.HTTP_200_OK,
    summary="List current user's workspaces",
)
async def list_workspaces(
    workspace_service: WorkspaceServiceDependency,
    current_user: VerifiedUser,
) -> WorkspaceListResponse:
    return await workspace_service.list_user_workspaces(
        user=current_user,
    )


# =========================================================
# PROVISION WORKSPACE TENANT
# =========================================================


@router.post(
    "/{workspace_id}/provision",
    response_model=WorkspaceProvisioningResponse,
    status_code=status.HTTP_200_OK,
    summary="Provision workspace tenant database",
)
async def provision_workspace(
    workspace_id: uuid.UUID,
    workspace_service: WorkspaceServiceDependency,
    current_user: VerifiedUser,
) -> WorkspaceProvisioningResponse:
    result = await workspace_service.provision_workspace(
        workspace_id=workspace_id,
        user=current_user,
    )

    return WorkspaceProvisioningResponse.model_validate(
        result
    )


# =========================================================
# RETRY WORKSPACE TENANT PROVISIONING
# =========================================================


@router.post(
    "/{workspace_id}/retry-provisioning",
    response_model=WorkspaceProvisioningRetryResponse,
    status_code=status.HTTP_200_OK,
    summary="Retry workspace tenant provisioning",
)
async def retry_workspace_provisioning(
    workspace_id: uuid.UUID,
    workspace_service: WorkspaceServiceDependency,
    current_user: VerifiedUser,
) -> WorkspaceProvisioningRetryResponse:
    result = (
        await workspace_service.retry_workspace_provisioning(
            workspace_id=workspace_id,
            user=current_user,
        )
    )

    return WorkspaceProvisioningRetryResponse.model_validate(
        result
    )


# =========================================================
# WORKSPACE DETAIL
# =========================================================
# =========================================================
# WORKSPACE BOOTSTRAP
# =========================================================


@router.get(
    "/{workspace_id}/bootstrap",
    response_model=WorkspaceBootstrapResponse,
    status_code=status.HTTP_200_OK,
    summary="Get workspace bootstrap context",
)
async def get_workspace_bootstrap(
    workspace_id: uuid.UUID,
    bootstrap_service: WorkspaceBootstrapServiceDependency,
    current_user: VerifiedUser,
) -> WorkspaceBootstrapResponse:
    return await (
        bootstrap_service
        .get_workspace_bootstrap(
            workspace_id=workspace_id,
            user=current_user,
        )
    )

@router.get(
    "/{workspace_id}",
    response_model=WorkspaceDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get workspace",
)
async def get_workspace(
    workspace_id: uuid.UUID,
    workspace_service: WorkspaceServiceDependency,
    current_user: VerifiedUser,
) -> WorkspaceDetailResponse:
    return await workspace_service.get_workspace(
        workspace_id=workspace_id,
        user=current_user,
    )


# =========================================================
# UPDATE WORKSPACE
# =========================================================


@router.patch(
    "/{workspace_id}",
    response_model=WorkspaceDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Update workspace",
)
async def update_workspace(
    workspace_id: uuid.UUID,
    payload: WorkspaceUpdateRequest,
    workspace_service: WorkspaceServiceDependency,
    current_user: VerifiedUser,
) -> WorkspaceDetailResponse:
    return await workspace_service.update_workspace(
        payload,
        workspace_id=workspace_id,
        user=current_user,
    )


# =========================================================
# MEMBERSHIP ROLE UPDATE
# =========================================================


@router.patch(
    "/{workspace_id}/memberships/{membership_id}/role",
    response_model=WorkspaceMembershipResponse,
    status_code=status.HTTP_200_OK,
    summary="Update workspace membership role",
)
async def update_membership_role(
    workspace_id: uuid.UUID,
    membership_id: uuid.UUID,
    payload: WorkspaceMembershipRoleUpdateRequest,
    workspace_service: WorkspaceServiceDependency,
    current_user: VerifiedUser,
) -> WorkspaceMembershipResponse:
    return await workspace_service.update_membership_role(
        payload,
        workspace_id=workspace_id,
        membership_id=membership_id,
        user=current_user,
    )


# =========================================================
# MEMBERSHIP STATUS UPDATE
# =========================================================


@router.patch(
    "/{workspace_id}/memberships/{membership_id}/status",
    response_model=WorkspaceMembershipResponse,
    status_code=status.HTTP_200_OK,
    summary="Update workspace membership status",
)
async def update_membership_status(
    workspace_id: uuid.UUID,
    membership_id: uuid.UUID,
    payload: WorkspaceMembershipStatusUpdateRequest,
    workspace_service: WorkspaceServiceDependency,
    current_user: VerifiedUser,
) -> WorkspaceMembershipResponse:
    return await workspace_service.update_membership_status(
        payload,
        workspace_id=workspace_id,
        membership_id=membership_id,
        user=current_user,
    )


# =========================================================
# REMOVE MEMBERSHIP
# =========================================================


@router.delete(
    "/{workspace_id}/memberships/{membership_id}",
    response_model=WorkspaceMembershipRemoveResponse,
    status_code=status.HTTP_200_OK,
    summary="Remove workspace membership",
)
async def remove_membership(
    workspace_id: uuid.UUID,
    membership_id: uuid.UUID,
    workspace_service: WorkspaceServiceDependency,
    current_user: VerifiedUser,
) -> WorkspaceMembershipRemoveResponse:
    return await workspace_service.remove_membership(
        workspace_id=workspace_id,
        membership_id=membership_id,
        user=current_user,
    )


# =========================================================
# SUSPEND WORKSPACE
# =========================================================


@router.post(
    "/{workspace_id}/suspend",
    response_model=WorkspaceStateResponse,
    status_code=status.HTTP_200_OK,
    summary="Suspend workspace",
)
async def suspend_workspace(
    workspace_id: uuid.UUID,
    workspace_service: WorkspaceServiceDependency,
    current_user: VerifiedUser,
) -> WorkspaceStateResponse:
    return await workspace_service.suspend_workspace(
        workspace_id=workspace_id,
        user=current_user,
    )


# =========================================================
# ARCHIVE WORKSPACE
# =========================================================


@router.post(
    "/{workspace_id}/archive",
    response_model=WorkspaceStateResponse,
    status_code=status.HTTP_200_OK,
    summary="Archive workspace",
)
async def archive_workspace(
    workspace_id: uuid.UUID,
    workspace_service: WorkspaceServiceDependency,
    current_user: VerifiedUser,
) -> WorkspaceStateResponse:
    return await workspace_service.archive_workspace(
        workspace_id=workspace_id,
        user=current_user,
    )


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "router",
]
# Company/Agency member directories retain the standard tenant/billing guards.
from .directory_router import router as workspace_directory_router
router.include_router(workspace_directory_router)

# Company logo upload and image delivery routes.
from .logo_router import router as workspace_logo_router
router.include_router(workspace_logo_router)
