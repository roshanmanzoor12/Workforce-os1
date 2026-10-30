from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


DesktopPlatform = Literal[
    "windows",
    "macos",
    "linux",
]


class DesktopAgentSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True,
    )


class DesktopAgentRegisterRequest(
    DesktopAgentSchema
):
    installation_id: uuid.UUID

    device_name: str = Field(
        min_length=1,
        max_length=255,
    )

    platform: DesktopPlatform

    os_version: str | None = Field(
        default=None,
        max_length=255,
    )

    agent_version: str = Field(
        min_length=1,
        max_length=100,
    )

    consent_acknowledged: bool

    consent_version: str = Field(
        min_length=1,
        max_length=100,
    )


class DesktopAgentHeartbeatRequest(
    DesktopAgentSchema
):
    agent_version: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    os_version: str | None = Field(
        default=None,
        max_length=255,
    )


class DesktopAgentDeviceResponse(
    DesktopAgentSchema
):
    id: uuid.UUID

    user_id: uuid.UUID

    employee_id: uuid.UUID

    installation_id: uuid.UUID

    device_name: str

    platform: str

    os_version: str | None

    agent_version: str

    status: str

    is_disabled: bool

    consent_version: str

    consent_at: datetime

    last_seen_at: datetime

    registered_at: datetime


class DesktopAgentDeviceListResponse(
    DesktopAgentSchema
):
    items: list[
        DesktopAgentDeviceResponse
    ] = Field(
        default_factory=list
    )

    total: int = Field(
        ge=0
    )

    limit: int = Field(
        ge=1,
        le=500,
    )

    offset: int = Field(
        ge=0
    )


class DesktopAgentHeartbeatResponse(
    DesktopAgentSchema
):
    device_id: uuid.UUID

    accepted: bool = True

    status: str

    last_seen_at: datetime


class DesktopAgentCapabilitiesResponse(
    DesktopAgentSchema
):
    device_registration: bool = True

    authenticated_heartbeat: bool = True

    consent_required: bool = True

    self_device_access: bool = True

    team_device_access: bool = True

    workspace_device_access: bool = True

    admin_disable: bool = True

    screenshot_capture: bool = False

    live_screen: bool = False

    captures_keystrokes: bool = False

    captures_clipboard: bool = False

    captures_passwords: bool = False

    captures_mouse_coordinates: bool = False


__all__ = [
    "DesktopAgentRegisterRequest",
    "DesktopAgentHeartbeatRequest",
    "DesktopAgentDeviceResponse",
    "DesktopAgentDeviceListResponse",
    "DesktopAgentHeartbeatResponse",
    "DesktopAgentCapabilitiesResponse",
]