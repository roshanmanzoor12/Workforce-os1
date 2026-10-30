from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import (
    Depends,
    Header,
    HTTPException,
    status,
)
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_control_db
from app.modules.devices.auth_service import (
    AuthenticatedDeviceContext,
    DeviceAuthService,
)
from app.modules.devices.credential_schemas import (
    DeviceAuthenticationRequest,
)


# =========================================================
# CONTROL DATABASE
# =========================================================

ControlDB = Annotated[
    AsyncSession,
    Depends(get_control_db),
]


# =========================================================
# DEVICE AUTH HEADERS
# =========================================================

DeviceUUIDHeader = Annotated[
    str,
    Header(
        alias="X-Device-UUID",
        min_length=1,
    ),
]

DeviceSecretHeader = Annotated[
    str,
    Header(
        alias="X-Device-Secret",
        min_length=1,
    ),
]


# =========================================================
# AUTHENTICATED DEVICE DEPENDENCY
# =========================================================


async def get_authenticated_device(
    control_db: ControlDB,
    device_uuid_header: DeviceUUIDHeader,
    device_secret_header: DeviceSecretHeader,
) -> AuthenticatedDeviceContext:
    """
    Authenticate a registered endpoint agent.

    Request headers:

        X-Device-UUID
        X-Device-Secret

    Authentication flow:

        device_uuid
            ↓
        control DeviceRoute
            ↓
        trusted workspace
            ↓
        trusted TenantDatabaseRegistry
            ↓
        tenant database identity verification
            ↓
        DeviceCredential verification
            ↓
        active tenant Device
            ↓
        AuthenticatedDeviceContext

    No database name, workspace ID, cluster key, or tenant-routing
    information is accepted from the endpoint.
    """

    # -----------------------------------------------------
    # PARSE UUID
    # -----------------------------------------------------

    try:
        device_uuid = uuid.UUID(
            device_uuid_header
        )

    except (
        ValueError,
        TypeError,
        AttributeError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Device authentication failed.",
            headers={
                "WWW-Authenticate": "Device",
            },
        ) from exc

    # -----------------------------------------------------
    # BUILD INTERNAL AUTH PAYLOAD
    # -----------------------------------------------------

    try:
        payload = DeviceAuthenticationRequest(
            device_uuid=device_uuid,
            device_secret=device_secret_header,
        )

    except PydanticValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Device authentication failed.",
            headers={
                "WWW-Authenticate": "Device",
            },
        ) from exc

    # -----------------------------------------------------
    # AUTHENTICATE
    # -----------------------------------------------------

    auth_service = DeviceAuthService(
        control_db
    )

    try:
        return await auth_service.authenticate_device(
            payload
        )

    except HTTPException:
        raise

    except Exception as exc:
        """
        Do not expose whether failure came from:

            unknown device_uuid
            revoked route
            wrong workspace
            stale tenant schema
            missing credential
            wrong device_secret
            revoked credential
            disabled/revoked device

        The agent receives one generic authentication failure.
        """

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Device authentication failed.",
            headers={
                "WWW-Authenticate": "Device",
            },
        ) from exc


# =========================================================
# TYPE ALIAS
# =========================================================

AuthenticatedDevice = Annotated[
    AuthenticatedDeviceContext,
    Depends(
        get_authenticated_device
    ),
]


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "ControlDB",
    "DeviceUUIDHeader",
    "DeviceSecretHeader",
    "AuthenticatedDevice",
    "get_authenticated_device",
]