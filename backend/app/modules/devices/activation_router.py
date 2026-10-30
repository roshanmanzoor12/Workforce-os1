from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Query,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_control_db
from app.core.exceptions import ValidationError
from app.modules.auth.models import User
from app.modules.auth.permissions import get_current_user
from app.modules.devices.activation_schemas import (
    DeviceActivationCodeCreateRequest,
    DeviceActivationCodeCreateResponse,
    DeviceActivationCodeListResponse,
    DeviceActivationCodeResponse,
    DeviceActivationCodeRevokeResponse,
)
from app.modules.devices.activation_service import (
    DeviceActivationService,
)
from app.modules.workspaces.models import (
    WORKSPACE_ROLE_ADMIN,
    WORKSPACE_ROLE_OWNER,
    WorkspaceMembership,
)
from app.modules.workspaces.service import WorkspaceService


router = APIRouter(
    prefix=(
        "/workspaces/{workspace_id}"
        "/device-activation-codes"
    ),
    tags=[
        "Device Activation Codes",
    ],
)


# =========================================================
# DEPENDENCY TYPES
# =========================================================


ControlDB = Annotated[
    AsyncSession,
    Depends(get_control_db),
]


CurrentUser = Annotated[
    User,
    Depends(get_current_user),
]


# =========================================================
# RBAC
# =========================================================


DEVICE_ACTIVATION_WRITE_ROLES = frozenset(
    {
        WORKSPACE_ROLE_OWNER,
        WORKSPACE_ROLE_ADMIN,
    }
)


def require_activation_write_access(
    membership: WorkspaceMembership,
) -> None:
    """
    Only workspace owner/admin may create or revoke
    endpoint enrollment codes.

    The role is obtained from trusted control-plane
    membership data, never from client request data.
    """

    if (
        membership.role_key
        not in DEVICE_ACTIVATION_WRITE_ROLES
    ):
        raise ValidationError(
            "Owner or admin workspace role is required "
            "to manage device activation codes."
        )


# =========================================================
# SERVICE FACTORIES
# =========================================================


def get_activation_service(
    db: ControlDB,
) -> DeviceActivationService:
    return DeviceActivationService(
        db
    )


def get_workspace_service(
    db: ControlDB,
) -> WorkspaceService:
    return WorkspaceService(
        db
    )


ActivationServiceDependency = Annotated[
    DeviceActivationService,
    Depends(get_activation_service),
]


WorkspaceServiceDependency = Annotated[
    WorkspaceService,
    Depends(get_workspace_service),
]


# =========================================================
# WORKSPACE AUTHORIZATION
# =========================================================


async def require_workspace_membership(
    *,
    workspace_id: uuid.UUID,
    current_user: User,
    workspace_service: WorkspaceService,
) -> WorkspaceMembership:
    """
    Resolve membership through the existing trusted
    WorkspaceService authorization path.

    Unknown / inaccessible workspaces remain hidden through
    the existing workspace service behavior.
    """

    (
        _workspace,
        membership,
        _tenant,
    ) = (
        await workspace_service.get_authorized_workspace_context(
            workspace_id=workspace_id,
            user=current_user,
        )
    )

    return membership


# =========================================================
# CREATE ACTIVATION CODE
# =========================================================


@router.post(
    "",
    response_model=DeviceActivationCodeCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create device activation code",
)
async def create_device_activation_code(
    workspace_id: uuid.UUID,
    payload: DeviceActivationCodeCreateRequest,
    current_user: CurrentUser,
    activation_service: ActivationServiceDependency,
    workspace_service: WorkspaceServiceDependency,
) -> DeviceActivationCodeCreateResponse:
    membership = (
        await require_workspace_membership(
            workspace_id=workspace_id,
            current_user=current_user,
            workspace_service=workspace_service,
        )
    )

    require_activation_write_access(
        membership
    )

    return (
        await activation_service.create_activation_code(
            payload,
            workspace_id=workspace_id,
            created_by_user_id=current_user.id,
        )
    )


# =========================================================
# LIST ACTIVATION CODES
# =========================================================


@router.get(
    "",
    response_model=DeviceActivationCodeListResponse,
    status_code=status.HTTP_200_OK,
    summary="List device activation codes",
)
async def list_device_activation_codes(
    workspace_id: uuid.UUID,
    current_user: CurrentUser,
    activation_service: ActivationServiceDependency,
    workspace_service: WorkspaceServiceDependency,
    include_inactive: Annotated[
        bool,
        Query(),
    ] = False,
) -> DeviceActivationCodeListResponse:
    await require_workspace_membership(
        workspace_id=workspace_id,
        current_user=current_user,
        workspace_service=workspace_service,
    )

    return (
        await activation_service.list_activation_codes(
            workspace_id=workspace_id,
            include_inactive=include_inactive,
        )
    )


# =========================================================
# GET ACTIVATION CODE
# =========================================================


@router.get(
    "/{activation_id}",
    response_model=DeviceActivationCodeResponse,
    status_code=status.HTTP_200_OK,
    summary="Get device activation code",
)
async def get_device_activation_code(
    workspace_id: uuid.UUID,
    activation_id: uuid.UUID,
    current_user: CurrentUser,
    activation_service: ActivationServiceDependency,
    workspace_service: WorkspaceServiceDependency,
) -> DeviceActivationCodeResponse:
    await require_workspace_membership(
        workspace_id=workspace_id,
        current_user=current_user,
        workspace_service=workspace_service,
    )

    return (
        await activation_service.get_activation_code(
            workspace_id=workspace_id,
            activation_id=activation_id,
        )
    )


# =========================================================
# REVOKE ACTIVATION CODE
# =========================================================


@router.delete(
    "/{activation_id}",
    response_model=DeviceActivationCodeRevokeResponse,
    status_code=status.HTTP_200_OK,
    summary="Revoke device activation code",
)
async def revoke_device_activation_code(
    workspace_id: uuid.UUID,
    activation_id: uuid.UUID,
    current_user: CurrentUser,
    activation_service: ActivationServiceDependency,
    workspace_service: WorkspaceServiceDependency,
) -> DeviceActivationCodeRevokeResponse:
    membership = (
        await require_workspace_membership(
            workspace_id=workspace_id,
            current_user=current_user,
            workspace_service=workspace_service,
        )
    )

    require_activation_write_access(
        membership
    )

    return (
        await activation_service.revoke_activation_code(
            workspace_id=workspace_id,
            activation_id=activation_id,
        )
    )


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "ControlDB",
    "CurrentUser",
    "DEVICE_ACTIVATION_WRITE_ROLES",
    "ActivationServiceDependency",
    "WorkspaceServiceDependency",
    "require_activation_write_access",
    "require_workspace_membership",
    "get_activation_service",
    "get_workspace_service",
    "create_device_activation_code",
    "list_device_activation_codes",
    "get_device_activation_code",
    "revoke_device_activation_code",
    "router",
]