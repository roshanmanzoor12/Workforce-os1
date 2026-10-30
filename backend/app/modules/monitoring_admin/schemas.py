from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class MonitoringAdminSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True,
    )


class MonitoringAdminPolicyUpdate(
    MonitoringAdminSchema
):
    monitoring_enabled: bool | None = None

    screenshots_enabled: bool | None = None

    live_screen_enabled: bool | None = None

    screen_share_enabled: bool | None = None

    disclosure_required: bool | None = None

    explicit_live_consent_required: (
        bool | None
    ) = None

    visible_live_indicator_required: (
        bool | None
    ) = None

    screenshot_interval_seconds: (
        int | None
    ) = Field(
        default=None,
        ge=1,
    )

    screenshot_retention_days: (
        int | None
    ) = Field(
        default=None,
        ge=1,
        le=3650,
    )

    live_session_max_minutes: (
        int | None
    ) = Field(
        default=None,
        ge=1,
        le=480,
    )

    policy_notice: str | None = Field(
        default=None,
        max_length=4000,
    )


class MonitoringAdminPolicyPublic(
    MonitoringAdminSchema
):
    id: uuid.UUID

    monitoring_enabled: bool

    screenshots_enabled: bool

    live_screen_enabled: bool

    screen_share_enabled: bool

    disclosure_required: bool

    explicit_live_consent_required: bool

    visible_live_indicator_required: bool

    screenshot_interval_seconds: int

    screenshot_retention_days: int

    live_session_max_minutes: int

    policy_version: int

    policy_notice: str | None

    updated_by_user_id: uuid.UUID | None

    created_at: datetime

    updated_at: datetime


class MonitoringPolicyCapabilities(
    MonitoringAdminSchema
):
    monitoring_allowed: bool

    screenshots_allowed: bool

    live_screen_allowed: bool

    screen_share_allowed: bool

    disclosure_required: bool

    explicit_live_consent_required: bool

    visible_live_indicator_required: bool

    screenshot_interval_seconds: int

    screenshot_retention_days: int

    live_session_max_minutes: int

    policy_version: int


class MonitoringPolicyAccessResponse(
    MonitoringAdminSchema
):
    can_view: bool

    can_manage: bool

    can_live_view: bool

    can_live_screen: bool

    can_manage_settings: bool


class MonitoringAdminSummaryResponse(
    MonitoringAdminSchema
):
    workspace_id: uuid.UUID

    policy: MonitoringAdminPolicyPublic

    capabilities: MonitoringPolicyCapabilities

    access: MonitoringPolicyAccessResponse



class MonitoringScreenshotRetentionCleanupResponse(
    MonitoringAdminSchema
):
    retention_days: int

    cutoff_at: datetime

    scanned: int

    deleted: int

    storage_failures: int

    database_failures: int

    has_more: bool

__all__ = [
    "MonitoringAdminPolicyUpdate",
    "MonitoringAdminPolicyPublic",
    "MonitoringPolicyCapabilities",
    "MonitoringPolicyAccessResponse",
    "MonitoringAdminSummaryResponse",
    "MonitoringScreenshotRetentionCleanupResponse",
]



