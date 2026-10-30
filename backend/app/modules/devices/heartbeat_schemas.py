from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


__all__ = [
    "DeviceHeartbeatRequest",
    "DeviceHeartbeatResponse",
]


class DeviceHeartbeatRequest(BaseModel):
    """
    Payload sent periodically by an authenticated WorkforceOS Agent.

    Device identity is intentionally NOT accepted from the request body.
    The backend resolves the device from authenticated device credentials.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    agent_version: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description=(
            "Currently running WorkforceOS Agent version."
        ),
    )

    hostname: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description=(
            "Current machine hostname. "
            "May be used to synchronize renamed devices."
        ),
    )


class DeviceHeartbeatResponse(BaseModel):
    """
    Server acknowledgement for a successful authenticated heartbeat.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    device_uuid: UUID

    status: str

    heartbeat_at: datetime

    next_heartbeat_seconds: int = Field(
        ge=5,
        le=300,
    )