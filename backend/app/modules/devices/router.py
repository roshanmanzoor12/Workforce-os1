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
from app.db.tenant_dependency import TenantScope
from app.modules.devices.management_service import (
    DeviceManagementService,
)
from app.modules.devices.schemas import (
    DeviceAssignmentRequest,
    DeviceDeleteResponse,
    DeviceDetailResponse,
    DeviceListResponse,
    DeviceResponse,
    DeviceStatus,
    DeviceUpdateRequest,
)
from app.modules.devices.service import DeviceService


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    prefix="/workspaces/{workspace_id}/devices",
    tags=["Devices"],
)


# =========================================================
# RBAC
# =========================================================

DEVICE_WRITE_ROLES = frozenset(
    {
        "owner",
        "admin",
    }
)


def get_scope_role(
    scope,
) -> str | None:
    """
    Resolve trusted workspace role from TenantRequestScope.

    Prefer a direct role_key if the scope exposes one, then
    fall back to the authorized tenant context.
    """

    direct_role = getattr(
        scope,
        "role_key",
        None,
    )

    if direct_role:
        return direct_role

    context = getattr(
        scope,
        "context",
        None,
    )

    if context is None:
        return None

    return getattr(
        context,
        "role_key",
        None,
    )


def require_device_write_access(
    scope,
) -> None:
    """
    Administrative device mutations require owner/admin access.

    Role comes only from trusted authorization scope.
    """

    role_key = get_scope_role(
        scope
    )

    if role_key not in DEVICE_WRITE_ROLES:
        raise ValidationError(
            "Owner or admin workspace role is required "
            "to manage devices."
        )


# =========================================================
# DEPENDENCY TYPES
# =========================================================

ControlDB = Annotated[
    AsyncSession,
    Depends(get_control_db),
]


# =========================================================
# TENANT DEVICE SERVICE
# =========================================================


def get_device_service(
    scope: TenantScope,
) -> DeviceService:
    return DeviceService(
        scope.session
    )


DeviceServiceDependency = Annotated[
    DeviceService,
    Depends(get_device_service),
]


# =========================================================
# CROSS-PLANE MANAGEMENT SERVICE
# =========================================================


def get_device_management_service(
    control_db: ControlDB,
) -> DeviceManagementService:
    return DeviceManagementService(
        control_db
    )


DeviceManagementServiceDependency = Annotated[
    DeviceManagementService,
    Depends(get_device_management_service),
]


# =========================================================
# LIST DEVICES
# =========================================================


@router.get(
    "",
    response_model=DeviceListResponse,
    status_code=status.HTTP_200_OK,
    summary="List workspace devices",
)
async def list_devices(
    scope: TenantScope,
    service: DeviceServiceDependency,
    employee_id: Annotated[
        uuid.UUID | None,
        Query(),
    ] = None,
    device_status: Annotated[
        DeviceStatus | None,
        Query(alias="status"),
    ] = None,
    include_inactive: Annotated[
        bool,
        Query(),
    ] = False,
    search: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=255,
        ),
    ] = None,
) -> DeviceListResponse:
    """
    List devices in the already-authorized tenant.

    Authorized workspace members may read device inventory.
    """

    return await service.list_devices(
        employee_id=employee_id,
        status=device_status,
        include_inactive=include_inactive,
        search=search,
    )


# =========================================================
# GET DEVICE
# =========================================================


@router.get(
    "/{device_id}",
    response_model=DeviceDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get workspace device",
)
async def get_device(
    device_id: uuid.UUID,
    scope: TenantScope,
    service: DeviceServiceDependency,
) -> DeviceDetailResponse:
    """
    Read one device from the authorized tenant.
    """

    return await service.get_device(
        device_id=device_id
    )


# =========================================================
# ASSIGN / UNASSIGN EMPLOYEE
# =========================================================


@router.patch(
    "/{device_id}/assignment",
    response_model=DeviceResponse,
    status_code=status.HTTP_200_OK,
    summary="Assign device to employee",
)
async def assign_device(
    device_id: uuid.UUID,
    payload: DeviceAssignmentRequest,
    scope: TenantScope,
    service: DeviceServiceDependency,
) -> DeviceResponse:
    """
    Assign or unassign a device.

    employee_id=None explicitly removes the assignment.
    """

    require_device_write_access(
        scope
    )

    return await service.assign_device(
        payload,
        device_id=device_id,
    )


# =========================================================
# UPDATE DEVICE
# =========================================================


@router.patch(
    "/{device_id}",
    response_model=DeviceResponse,
    status_code=status.HTTP_200_OK,
    summary="Update workspace device",
)
async def update_device(
    device_id: uuid.UUID,
    payload: DeviceUpdateRequest,
    scope: TenantScope,
    service: DeviceServiceDependency,
) -> DeviceResponse:
    """
    Administrative device update.

    Lifecycle transition to revoked also revokes tenant-side
    credentials through DeviceService.
    """

    require_device_write_access(
        scope
    )

    return await service.update_device(
        payload,
        device_id=device_id,
    )


# =========================================================
# REVOKE DEVICE
# =========================================================


@router.delete(
    "/{device_id}",
    response_model=DeviceDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Revoke workspace device",
)
async def revoke_device(
    workspace_id: uuid.UUID,
    device_id: uuid.UUID,
    scope: TenantScope,
    service: DeviceServiceDependency,
    management_service: DeviceManagementServiceDependency,
) -> DeviceDeleteResponse:
    """
    Revoke a registered endpoint across tenant and control planes.

    Sequence:

        authorized tenant lookup
            ↓
        resolve trusted device_uuid
            ↓
        revoke Device + credentials in tenant DB
            ↓
        revoke DeviceRoute in control DB

    Hard deletion is intentionally avoided so historical monitoring
    and audit records remain attributable to the endpoint.
    """

    require_device_write_access(
        scope
    )

    # -----------------------------------------------------
    # Resolve trusted device identity from tenant DB
    # -----------------------------------------------------

    device_detail = await service.get_device(
        device_id=device_id
    )

    device_uuid = (
        device_detail.device.device_uuid
    )

    # -----------------------------------------------------
    # Cross-plane revocation
    # -----------------------------------------------------

    return await management_service.revoke_device(
        workspace_id=workspace_id,
        device_id=device_id,
        device_uuid=device_uuid,
    )


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "DEVICE_WRITE_ROLES",
    "ControlDB",
    "DeviceServiceDependency",
    "DeviceManagementServiceDependency",
    "get_scope_role",
    "require_device_write_access",
    "get_device_service",
    "get_device_management_service",
    "list_devices",
    "get_device",
    "assign_device",
    "update_device",
    "revoke_device",
    "router",
]