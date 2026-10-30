from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


# =========================================================
# BASE
# =========================================================


class EmployeeMonitoringSchema(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True,
    )


# =========================================================
# EMPLOYEE
# =========================================================


class EmployeeMonitoringEmployee(
    EmployeeMonitoringSchema
):
    id: uuid.UUID

    full_name: str

    job_title: str | None = None

    avatar_url: str | None = None

    employment_status: str

    department_id: uuid.UUID | None = None
    department_name: str | None = None

    team_id: uuid.UUID | None = None
    team_name: str | None = None


# =========================================================
# ACTIVITY
# =========================================================


class EmployeeMonitoringActivity(
    EmployeeMonitoringSchema
):
    state: str | None = None

    idle_seconds: int = Field(
        default=0,
        ge=0,
    )

    observed_at: datetime | None = None

    received_at: datetime | None = None


# =========================================================
# APPLICATIONS
# =========================================================


class EmployeeMonitoringAppItem(
    EmployeeMonitoringSchema
):
    id: uuid.UUID

    device_id: uuid.UUID

    app_key: str

    process_name: str

    status: str

    started_at: datetime

    ended_at: datetime | None = None

    last_observed_at: datetime

    duration_seconds: int = Field(
        ge=0,
    )


# =========================================================
# WEBSITES
# =========================================================


class EmployeeMonitoringWebsiteItem(
    EmployeeMonitoringSchema
):
    id: uuid.UUID

    device_id: uuid.UUID

    browser_name: str

    domain: str

    normalized_domain: str

    status: str

    started_at: datetime

    ended_at: datetime | None = None

    last_observed_at: datetime

    duration_seconds: int = Field(
        ge=0,
    )


# =========================================================
# WORK SESSIONS
# =========================================================


class EmployeeMonitoringWorkSession(
    EmployeeMonitoringSchema
):
    id: uuid.UUID

    device_id: uuid.UUID

    status: str

    current_state: str

    started_at: datetime

    ended_at: datetime | None = None

    last_observed_at: datetime

    active_seconds: int = Field(
        ge=0,
    )

    idle_seconds: int = Field(
        ge=0,
    )

    total_seconds: int = Field(
        ge=0,
    )


# =========================================================
# DEVICES
# =========================================================


class EmployeeMonitoringDevice(
    EmployeeMonitoringSchema
):
    id: uuid.UUID

    device_name: str

    platform: str

    os_version: str | None = None

    agent_version: str

    status: str

    is_disabled: bool

    last_seen_at: datetime

    registered_at: datetime

    capabilities: dict = Field(
        default_factory=dict,
    )


# =========================================================
# SCREENSHOT HISTORY
# =========================================================


class EmployeeMonitoringScreenshot(
    EmployeeMonitoringSchema
):
    id: uuid.UUID

    device_id: uuid.UUID

    status: str

    reason: str | None = None

    consent_required: bool

    visible_indicator_required: bool

    consent_confirmed_at: (
        datetime
        | None
    ) = None

    requested_at: datetime

    expires_at: datetime

    completed_at: datetime | None = None

    width: int | None = None

    height: int | None = None


# =========================================================
# RESPONSE
# =========================================================


class EmployeeMonitoringDetailResponse(
    EmployeeMonitoringSchema
):
    employee: EmployeeMonitoringEmployee

    current_activity: (
        EmployeeMonitoringActivity
        | None
    ) = None

    devices: list[
        EmployeeMonitoringDevice
    ] = Field(
        default_factory=list,
    )

    applications: list[
        EmployeeMonitoringAppItem
    ] = Field(
        default_factory=list,
    )

    websites: list[
        EmployeeMonitoringWebsiteItem
    ] = Field(
        default_factory=list,
    )

    work_sessions: list[
        EmployeeMonitoringWorkSession
    ] = Field(
        default_factory=list,
    )

    screenshots: list[
        EmployeeMonitoringScreenshot
    ] = Field(
        default_factory=list,
    )

    screens_allowed: bool = False

    device_count: int = Field(
        default=0,
        ge=0,
    )

    application_count: int = Field(
        default=0,
        ge=0,
    )

    website_count: int = Field(
        default=0,
        ge=0,
    )

    work_session_count: int = Field(
        default=0,
        ge=0,
    )

    screenshot_count: int = Field(
        default=0,
        ge=0,
    )


__all__ = [
    "EmployeeMonitoringEmployee",
    "EmployeeMonitoringActivity",
    "EmployeeMonitoringAppItem",
    "EmployeeMonitoringWebsiteItem",
    "EmployeeMonitoringWorkSession",
    "EmployeeMonitoringDevice",
    "EmployeeMonitoringScreenshot",
    "EmployeeMonitoringDetailResponse",
]