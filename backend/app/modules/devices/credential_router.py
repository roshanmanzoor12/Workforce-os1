from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Query,
    status,
)

from app.core.exceptions import ValidationError
from app.db.tenant_dependency import TenantScope
from app.modules.devices.credential_schemas import (
    DeviceCredentialListResponse,
    DeviceCredentialRevokeResponse,
    DeviceCredentialRotationResponse,
)
from app.modules.devices.credential_service import (
    DeviceCredentialService,
)


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    prefix=(
        "/workspaces/{workspace_id}"
        "/devices/{device_id}/credentials"
    ),
    tags=["Device Credentials"],
)


# =========================================================
# RBAC
# =========================================================

DEVICE_CREDENTIAL_WRITE_ROLES = frozenset(
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

    Prefer direct role_key if present, otherwise fall back to
    the authorized tenant context.
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


def require_device_credential_write_access(
    scope,
) -> None:
    """
    Credential operations are restricted to workspace owner/admin.

    Role comes only from trusted tenant authorization state.
    """

    role_key = get_scope_role(
        scope
    )

    if (
        role_key
        not in DEVICE_CREDENTIAL_WRITE_ROLES
    ):
        raise ValidationError(
            "Owner or admin workspace role is required "
            "to manage device credentials."
        )


# =========================================================
# SERVICE FACTORY
# =========================================================


def get_device_credential_service(
    scope: TenantScope,
) -> DeviceCredentialService:
    return DeviceCredentialService(
        scope.session
    )


DeviceCredentialServiceDependency = Annotated[
    DeviceCredentialService,
    Depends(
        get_device_credential_service
    ),
]


# =========================================================
# LIST CREDENTIAL HISTORY
# =========================================================


@router.get(
    "",
    response_model=DeviceCredentialListResponse,
    status_code=status.HTTP_200_OK,
    summary="List device credentials",
)
async def list_device_credentials(
    device_id: uuid.UUID,
    scope: TenantScope,
    service: DeviceCredentialServiceDependency,
    include_inactive: Annotated[
        bool,
        Query(),
    ] = True,
) -> DeviceCredentialListResponse:
    """
    List safe credential metadata for one device.

    Plaintext secrets and secret hashes are never returned.
    """

    require_device_credential_write_access(
        scope
    )

    return await service.list_credentials(
        device_id=device_id,
        include_inactive=include_inactive,
    )


# =========================================================
# ROTATE CREDENTIAL
# =========================================================


@router.post(
    "/rotate",
    response_model=DeviceCredentialRotationResponse,
    status_code=status.HTTP_200_OK,
    summary="Rotate device credential",
)
async def rotate_device_credential(
    device_id: uuid.UUID,
    scope: TenantScope,
    service: DeviceCredentialServiceDependency,
) -> DeviceCredentialRotationResponse:
    """
    Revoke currently active credential(s) and issue a replacement.

    The new plaintext device secret is returned exactly once.
    """

    require_device_credential_write_access(
        scope
    )

    return await service.rotate_credential(
        device_id=device_id
    )


# =========================================================
# REVOKE ONE CREDENTIAL
# =========================================================


@router.delete(
    "/{credential_id}",
    response_model=DeviceCredentialRevokeResponse,
    status_code=status.HTTP_200_OK,
    summary="Revoke device credential",
)
async def revoke_device_credential(
    device_id: uuid.UUID,
    credential_id: uuid.UUID,
    scope: TenantScope,
    service: DeviceCredentialServiceDependency,
) -> DeviceCredentialRevokeResponse:
    """
    Revoke one credential belonging to this device.
    """

    require_device_credential_write_access(
        scope
    )

    return await service.revoke_credential(
        device_id=device_id,
        credential_id=credential_id,
    )


# =========================================================
# REVOKE ALL ACTIVE CREDENTIALS
# =========================================================


@router.delete(
    "",
    response_model=DeviceCredentialRevokeResponse,
    status_code=status.HTTP_200_OK,
    summary="Revoke all device credentials",
)
async def revoke_all_device_credentials(
    device_id: uuid.UUID,
    scope: TenantScope,
    service: DeviceCredentialServiceDependency,
) -> DeviceCredentialRevokeResponse:
    """
    Revoke every currently active credential for a device.
    """

    require_device_credential_write_access(
        scope
    )

    return (
        await service.revoke_all_device_credentials(
            device_id=device_id
        )
    )


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "DEVICE_CREDENTIAL_WRITE_ROLES",
    "DeviceCredentialServiceDependency",
    "get_scope_role",
    "require_device_credential_write_access",
    "get_device_credential_service",
    "list_device_credentials",
    "rotate_device_credential",
    "revoke_device_credential",
    "revoke_all_device_credentials",
    "router",
]