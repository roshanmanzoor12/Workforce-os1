from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class LiveMonitoringSchema(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True,
    )


class ScreenshotRequestCreate(
    LiveMonitoringSchema
):
    device_id: uuid.UUID

    reason: str | None = Field(
        default=None,
        max_length=500,
    )


class ScreenshotAgentComplete(
    LiveMonitoringSchema
):
    consent_confirmed: bool

    visible_indicator_shown: bool

    storage_object_key: str = Field(
        min_length=1,
        max_length=1024,
    )

    sha256: str = Field(
        min_length=64,
        max_length=64,
    )

    width: int | None = Field(
        default=None,
        ge=1,
        le=32768,
    )

    height: int | None = Field(
        default=None,
        ge=1,
        le=32768,
    )


class ScreenshotAgentDeny(
    LiveMonitoringSchema
):
    reason: str | None = Field(
        default=None,
        max_length=500,
    )


class ScreenshotAgentFail(
    LiveMonitoringSchema
):
    reason: str = Field(
        min_length=1,
        max_length=1000,
    )


class ScreenshotResponse(
    LiveMonitoringSchema
):
    id: uuid.UUID

    device_id: uuid.UUID

    employee_id: uuid.UUID

    requested_by_user_id: uuid.UUID

    status: str

    reason: str | None

    visible_indicator_required: bool

    consent_required: bool

    consent_confirmed_at: (
        datetime
        | None
    )

    requested_at: datetime

    expires_at: datetime

    completed_at: (
        datetime
        | None
    )

    width: (
        int
        | None
    )

    height: (
        int
        | None
    )


class ScreenshotListResponse(
    LiveMonitoringSchema
):
    items: list[
        ScreenshotResponse
    ] = Field(
        default_factory=list
    )

    total: int = Field(
        ge=0
    )


class ScreenshotMediaResponse(
    LiveMonitoringSchema
):
    request_id: uuid.UUID

    download_url: str = Field(
        min_length=1,
    )

    expires_in_seconds: int = Field(
        ge=1,
        le=3600,
    )


class LiveScreenRequestCreate(
    LiveMonitoringSchema
):
    device_id: uuid.UUID

    reason: str | None = Field(
        default=None,
        max_length=500,
    )


class LiveScreenDecision(
    LiveMonitoringSchema
):
    accepted: bool

    visible_indicator_shown: bool


class LiveScreenActivateRequest(
    LiveMonitoringSchema
):
    session_channel: str = Field(
        min_length=1,
        max_length=255,
    )


class LiveScreenEndRequest(
    LiveMonitoringSchema
):
    reason: str | None = Field(
        default=None,
        max_length=1000,
    )


class LiveScreenResponse(
    LiveMonitoringSchema
):
    id: uuid.UUID

    device_id: uuid.UUID

    employee_id: uuid.UUID

    requested_by_user_id: uuid.UUID

    status: str

    reason: str | None

    consent_required: bool

    visible_indicator_required: bool

    accepted_at: (
        datetime
        | None
    )

    started_at: (
        datetime
        | None
    )

    ended_at: (
        datetime
        | None
    )

    expires_at: datetime

    transport: str

    session_channel: (
        str
        | None
    )

    end_reason: (
        str
        | None
    )


class LiveMonitoringCapabilitiesResponse(
    LiveMonitoringSchema
):
    screenshot_requests: bool = True

    screenshot_requires_consent: bool = True

    screenshot_visible_indicator: bool = True

    live_screen_requests: bool = True

    live_screen_requires_acceptance: bool = True

    live_screen_visible_indicator: bool = True

    live_screen_transport: str = "webrtc"

    captures_keystrokes: bool = False

    captures_clipboard: bool = False

    captures_passwords: bool = False

    captures_mouse_coordinates: bool = False


__all__ = [
    "ScreenshotRequestCreate",
    "ScreenshotAgentComplete",
    "ScreenshotAgentDeny",
    "ScreenshotAgentFail",
    "ScreenshotResponse",
    "ScreenshotListResponse",
    "ScreenshotMediaResponse",
    "LiveScreenRequestCreate",
    "LiveScreenDecision",
    "LiveScreenActivateRequest",
    "LiveScreenEndRequest",
    "LiveScreenResponse",
    "LiveMonitoringCapabilitiesResponse",
]

