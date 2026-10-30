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


# =========================================================
# ACTIVATION STATUS TYPE
# =========================================================

ActivationStatus = Literal[
    "active",
    "expired",
    "revoked",
    "exhausted",
]


# =========================================================
# BASE SCHEMA
# =========================================================


class DeviceActivationSchemaBase(
    BaseModel
):
    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )


# =========================================================
# CREATE ACTIVATION CODE
# =========================================================


class DeviceActivationCodeCreateRequest(
    DeviceActivationSchemaBase
):
    """
    Admin request for creating a new device activation code.

    The server generates the actual secret activation code.
    """

    label: str | None = Field(
        default=None,
        max_length=150,
    )

    expires_at: datetime | None = None

    max_uses: int | None = Field(
        default=None,
        gt=0,
    )

    @field_validator(
        "label",
    )
    @classmethod
    def normalize_label(
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
# ACTIVATION CODE PUBLIC MODEL
# =========================================================


class DeviceActivationCodePublic(
    DeviceActivationSchemaBase
):
    id: uuid.UUID

    workspace_id: uuid.UUID

    created_by_user_id: uuid.UUID

    code_prefix: str | None

    status: ActivationStatus

    is_active: bool

    expires_at: datetime | None

    revoked_at: datetime | None

    last_used_at: datetime | None

    max_uses: int | None

    used_count: int

    label: str | None

    created_at: datetime

    updated_at: datetime


# =========================================================
# CREATE RESPONSE
# =========================================================


class DeviceActivationCodeCreateResponse(
    DeviceActivationSchemaBase
):
    """
    Secret activation code is returned only at creation time.

    code_hash is never exposed.
    """

    message: str = (
        "Device activation code created."
    )

    activation_code: str = Field(
        min_length=6,
        max_length=200,
    )

    activation: DeviceActivationCodePublic


# =========================================================
# LIST RESPONSE
# =========================================================


class DeviceActivationCodeListResponse(
    DeviceActivationSchemaBase
):
    activation_codes: list[
        DeviceActivationCodePublic
    ]

    total: int = Field(
        ge=0,
    )


# =========================================================
# DETAIL RESPONSE
# =========================================================


class DeviceActivationCodeResponse(
    DeviceActivationSchemaBase
):
    activation: DeviceActivationCodePublic


# =========================================================
# REVOKE RESPONSE
# =========================================================


class DeviceActivationCodeRevokeResponse(
    DeviceActivationSchemaBase
):
    message: str

    success: bool


# =========================================================
# TRUSTED RESOLUTION RESULT
# =========================================================


class ResolvedDeviceActivation(
    DeviceActivationSchemaBase
):
    """
    Internal trusted activation result.

    This is not intended as a public agent response.

    It contains only control-plane identity needed to continue
    server-side tenant resolution.
    """

    activation_id: uuid.UUID

    workspace_id: uuid.UUID

    status: ActivationStatus

    expires_at: datetime | None

    max_uses: int | None

    used_count: int


# =========================================================
# ACTIVATION VALIDATION RESPONSE
# =========================================================


class DeviceActivationValidationResult(
    DeviceActivationSchemaBase
):
    valid: bool

    workspace_id: uuid.UUID | None = None

    activation_id: uuid.UUID | None = None


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "ActivationStatus",
    "DeviceActivationCodeCreateRequest",
    "DeviceActivationCodePublic",
    "DeviceActivationCodeCreateResponse",
    "DeviceActivationCodeListResponse",
    "DeviceActivationCodeResponse",
    "DeviceActivationCodeRevokeResponse",
    "ResolvedDeviceActivation",
    "DeviceActivationValidationResult",
]