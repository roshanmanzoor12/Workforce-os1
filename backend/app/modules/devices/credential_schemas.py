from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


# =========================================================
# DEVICE CREDENTIAL STATUS TYPE
# =========================================================

DeviceCredentialStatus = Literal[
    "active",
    "revoked",
    "expired",
]


# =========================================================
# BASE SCHEMA
# =========================================================


class DeviceCredentialSchemaBase(
    BaseModel
):
    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )


# =========================================================
# PUBLIC CREDENTIAL METADATA
# =========================================================


class DeviceCredentialPublic(
    DeviceCredentialSchemaBase
):
    """
    Safe credential metadata.

    secret_hash is intentionally never exposed.
    """

    id: uuid.UUID

    device_id: uuid.UUID

    secret_prefix: str | None

    version: int = Field(
        ge=1,
    )

    status: DeviceCredentialStatus

    is_active: bool

    issued_at: datetime | None

    expires_at: datetime | None

    revoked_at: datetime | None

    last_used_at: datetime | None

    created_at: datetime

    updated_at: datetime


# =========================================================
# INITIAL CREDENTIAL ISSUE RESULT
# =========================================================


class DeviceCredentialIssueResult(
    DeviceCredentialSchemaBase
):
    """
    Internal result returned when a new device secret is issued.

    device_secret is plaintext and must only be returned once.
    """

    device_secret: str = Field(
        min_length=20,
        max_length=255,
    )

    credential: DeviceCredentialPublic


# =========================================================
# AGENT AUTHENTICATION REQUEST
# =========================================================


class DeviceAuthenticationRequest(
    DeviceCredentialSchemaBase
):
    """
    Authentication material submitted by a registered agent.

    The device supplies:

        device_uuid
        device_secret

    Tenant routing must still be resolved server-side.
    """

    device_uuid: uuid.UUID

    device_secret: str = Field(
        min_length=20,
        max_length=255,
    )


# =========================================================
# AUTHENTICATION RESULT
# =========================================================


class AuthenticatedDeviceCredential(
    DeviceCredentialSchemaBase
):
    """
    Internal trusted authentication result.

    This is not intended as a public dashboard response.
    """

    device_id: uuid.UUID

    device_uuid: uuid.UUID

    credential_id: uuid.UUID

    credential_version: int = Field(
        ge=1,
    )


# =========================================================
# ROTATION RESPONSE
# =========================================================


class DeviceCredentialRotationResponse(
    DeviceCredentialSchemaBase
):
    """
    Plaintext replacement secret is returned exactly once.
    """

    message: str = (
        "Device credential rotated."
    )

    device_secret: str = Field(
        min_length=20,
        max_length=255,
    )

    credential: DeviceCredentialPublic


# =========================================================
# REVOKE RESPONSE
# =========================================================


class DeviceCredentialRevokeResponse(
    DeviceCredentialSchemaBase
):
    message: str

    success: bool


# =========================================================
# LIST RESPONSE
# =========================================================


class DeviceCredentialListResponse(
    DeviceCredentialSchemaBase
):
    credentials: list[
        DeviceCredentialPublic
    ]

    total: int = Field(
        ge=0,
    )


# =========================================================
# REGISTRATION CREDENTIAL
# =========================================================


class DeviceRegistrationCredential(
    DeviceCredentialSchemaBase
):
    """
    Credential material returned to the agent during first
    successful enrollment.

    The secret is never retrievable again from the backend.
    """

    device_uuid: uuid.UUID

    device_secret: str = Field(
        min_length=20,
        max_length=255,
    )


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "DeviceCredentialStatus",
    "DeviceCredentialPublic",
    "DeviceCredentialIssueResult",
    "DeviceAuthenticationRequest",
    "AuthenticatedDeviceCredential",
    "DeviceCredentialRotationResponse",
    "DeviceCredentialRevokeResponse",
    "DeviceCredentialListResponse",
    "DeviceRegistrationCredential",
]