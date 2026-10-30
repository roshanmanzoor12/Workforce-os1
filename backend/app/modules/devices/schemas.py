from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from app.modules.devices.credential_schemas import (
    DeviceRegistrationCredential,
)


# =========================================================
# DEVICE STATUS TYPE
# =========================================================

DeviceStatus = Literal[
    "pending",
    "active",
    "offline",
    "disabled",
    "revoked",
]


# =========================================================
# BASE SCHEMA
# =========================================================


class DeviceSchemaBase(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )


# =========================================================
# PUBLIC AGENT REGISTRATION
# =========================================================


class DeviceRegistrationRequest(
    DeviceSchemaBase
):
    """
    First-time endpoint enrollment payload.

    Agent may provide only machine/agent metadata plus the
    activation code.

    Agent cannot provide trusted tenant-routing data or its own
    trusted device identity.
    """

    activation_code: str = Field(
        min_length=6,
        max_length=200,
    )

    hostname: str = Field(
        min_length=1,
        max_length=255,
    )

    os_name: str = Field(
        min_length=1,
        max_length=100,
    )

    os_version: str | None = Field(
        default=None,
        max_length=100,
    )

    architecture: str | None = Field(
        default=None,
        max_length=50,
    )

    agent_version: str | None = Field(
        default=None,
        max_length=50,
    )

    agent_identifier: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    @field_validator(
        "activation_code",
        "hostname",
        "os_name",
    )
    @classmethod
    def normalize_required_text(
        cls,
        value: str,
    ) -> str:
        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "Value cannot be empty."
            )

        return normalized

    @field_validator(
        "os_version",
        "architecture",
        "agent_version",
        "agent_identifier",
    )
    @classmethod
    def normalize_optional_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = value.strip()

        if not normalized:
            return None

        return normalized


# =========================================================
# EMPLOYEE ASSIGNMENT
# =========================================================


class DeviceAssignmentRequest(
    DeviceSchemaBase
):
    """
    Assign or unassign a registered device.

    employee_id=None explicitly removes the current assignment.
    """

    employee_id: uuid.UUID | None


# =========================================================
# ADMIN UPDATE
# =========================================================


class DeviceUpdateRequest(
    DeviceSchemaBase
):
    """
    Owner/admin-controlled mutable fields.

    Trusted device identity and agent authentication credentials
    cannot be modified through this payload.
    """

    hostname: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    employee_id: uuid.UUID | None = None

    status: DeviceStatus | None = None

    is_active: bool | None = None

    monitoring_profile_id: uuid.UUID | None = None

    @field_validator(
        "hostname",
    )
    @classmethod
    def normalize_hostname(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "Hostname cannot be empty."
            )

        return normalized


# =========================================================
# AGENT METADATA UPDATE
# =========================================================


class DeviceAgentMetadataRequest(
    DeviceSchemaBase
):
    """
    Metadata an authenticated endpoint agent may refresh later.

    This does not permit modification of:

        employee_id
        device status
        active state
        monitoring profile
        device_uuid
        credentials
    """

    hostname: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    os_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    os_version: str | None = Field(
        default=None,
        max_length=100,
    )

    architecture: str | None = Field(
        default=None,
        max_length=50,
    )

    agent_version: str | None = Field(
        default=None,
        max_length=50,
    )

    agent_identifier: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    @field_validator(
        "hostname",
        "os_name",
    )
    @classmethod
    def normalize_required_if_present(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "Value cannot be empty."
            )

        return normalized

    @field_validator(
        "os_version",
        "architecture",
        "agent_version",
        "agent_identifier",
    )
    @classmethod
    def normalize_optional_agent_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = value.strip()

        if not normalized:
            return None

        return normalized


# =========================================================
# PUBLIC DEVICE
# =========================================================


class DevicePublic(
    DeviceSchemaBase
):
    id: uuid.UUID

    device_uuid: uuid.UUID

    employee_id: uuid.UUID | None

    hostname: str

    os_name: str

    os_version: str | None

    architecture: str | None

    agent_version: str | None

    agent_identifier: str | None

    status: DeviceStatus

    is_active: bool

    first_seen_at: datetime | None

    last_seen_at: datetime | None

    registered_at: datetime | None

    revoked_at: datetime | None

    monitoring_profile_id: uuid.UUID | None

    created_at: datetime

    updated_at: datetime


# =========================================================
# DEVICE DETAIL
# =========================================================


class DeviceDetailResponse(
    DeviceSchemaBase
):
    device: DevicePublic


# =========================================================
# DEVICE LIST
# =========================================================


class DeviceListResponse(
    DeviceSchemaBase
):
    devices: list[
        DevicePublic
    ]

    total: int = Field(
        ge=0,
    )


# =========================================================
# REGISTRATION RESPONSE
# =========================================================


class DeviceRegistrationResponse(
    DeviceSchemaBase
):
    """
    Returned only after the complete enrollment flow succeeds.

    credential.device_secret is plaintext and must be persisted
    securely by the installed agent immediately.

    The backend stores only the secret hash, so the plaintext
    secret cannot be retrieved again later.
    """

    message: str = (
        "Device registered."
    )

    device: DevicePublic

    credential: DeviceRegistrationCredential


# =========================================================
# STANDARD MUTATION RESPONSE
# =========================================================


class DeviceResponse(
    DeviceSchemaBase
):
    message: str

    device: DevicePublic


# =========================================================
# DEVICE REVOCATION RESPONSE
# =========================================================


class DeviceDeleteResponse(
    DeviceSchemaBase
):
    message: str

    success: bool


# =========================================================
# DEVICE STATUS RESPONSE
# =========================================================


class DeviceStatusResponse(
    DeviceSchemaBase
):
    device_id: uuid.UUID

    device_uuid: uuid.UUID

    status: DeviceStatus

    is_active: bool

    last_seen_at: datetime | None


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "DeviceStatus",
    "DeviceRegistrationRequest",
    "DeviceAssignmentRequest",
    "DeviceUpdateRequest",
    "DeviceAgentMetadataRequest",
    "DevicePublic",
    "DeviceDetailResponse",
    "DeviceListResponse",
    "DeviceRegistrationResponse",
    "DeviceResponse",
    "DeviceDeleteResponse",
    "DeviceStatusResponse",
]