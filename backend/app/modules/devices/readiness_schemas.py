from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from app.modules.devices.readiness_types import (
    DeviceReadinessStatus,
)


# =========================================================
# BASE
# =========================================================


class DeviceReadinessSchema(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
    )


# =========================================================
# DEVICE READINESS ROW
# =========================================================


class DeviceReadinessItem(
    DeviceReadinessSchema
):
    """
    Browser-safe device readiness projection.

    Deliberately excluded:

    - device secret
    - credential hash
    - credential material
    - IP address
    - database routing data
    """

    device_id: uuid.UUID

    employee_id: uuid.UUID

    device_name: str

    platform: str

    os_version: str | None

    agent_version: str

    status: DeviceReadinessStatus

    last_seen_at: datetime

    heartbeat_age_seconds: (
        int
        | None
    )

    is_online: bool

    consent_granted: bool

    activity_capability: bool

    screen_capability: bool

    monitoring_ready: bool

    live_ready: bool

    needs_setup: bool

    setup_reasons: list[
        str
    ] = Field(
        default_factory=list
    )


# =========================================================
# SUMMARY
# =========================================================


class DeviceReadinessSummary(
    DeviceReadinessSchema
):
    total: int = Field(
        ge=0
    )

    online: int = Field(
        ge=0
    )

    offline: int = Field(
        ge=0
    )

    disabled: int = Field(
        ge=0
    )

    monitoring_ready: int = Field(
        ge=0
    )

    live_ready: int = Field(
        ge=0
    )

    needs_setup: int = Field(
        ge=0
    )

    online_timeout_seconds: int = Field(
        ge=1
    )


# =========================================================
# COMPLETE RESPONSE
# =========================================================


class DeviceReadinessResponse(
    DeviceReadinessSchema
):
    summary: DeviceReadinessSummary

    devices: list[
        DeviceReadinessItem
    ] = Field(
        default_factory=list
    )


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "DeviceReadinessItem",
    "DeviceReadinessSummary",
    "DeviceReadinessResponse",
]