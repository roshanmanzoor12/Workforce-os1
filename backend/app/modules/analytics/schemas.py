from __future__ import annotations

import uuid
from datetime import (
    date,
    datetime,
)

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class AnalyticsSchema(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True,
    )


class AnalyticsWindow(
    AnalyticsSchema
):
    start_at: datetime
    end_at: datetime


class AnalyticsSeriesPoint(
    AnalyticsSchema
):
    date: date
    value: float


class AnalyticsNamedUsage(
    AnalyticsSchema
):
    name: str
    duration_seconds: int
    event_count: int = 0


class AnalyticsOverviewResponse(
    AnalyticsSchema
):
    workspace_id: uuid.UUID
    scope: str
    window: AnalyticsWindow

    employees: int = 0

    activity_events: int = 0
    active_events: int = 0
    idle_events: int = 0

    attendance_records: int = 0
    worked_minutes: int = 0

    app_intervals: int = 0
    app_seconds: int = 0

    website_intervals: int = 0
    website_seconds: int = 0

    goals_total: int = 0
    goals_completed: int = 0
    goals_average_progress: float = 0.0


class AnalyticsActivityResponse(
    AnalyticsSchema
):
    workspace_id: uuid.UUID
    scope: str
    window: AnalyticsWindow

    total_events: int = 0
    active_events: int = 0
    idle_events: int = 0

    average_idle_seconds: float = 0.0

    daily: list[
        AnalyticsSeriesPoint
    ] = Field(
        default_factory=list
    )


class AnalyticsAttendanceResponse(
    AnalyticsSchema
):
    workspace_id: uuid.UUID
    scope: str
    window: AnalyticsWindow

    total_records: int = 0
    worked_minutes: int = 0
    break_minutes: int = 0

    status_breakdown: dict[
        str,
        int,
    ] = Field(
        default_factory=dict
    )

    daily: list[
        AnalyticsSeriesPoint
    ] = Field(
        default_factory=list
    )


class AnalyticsProductivityResponse(
    AnalyticsSchema
):
    workspace_id: uuid.UUID
    scope: str
    window: AnalyticsWindow

    activity_events: int = 0

    active_events: int = 0
    idle_events: int = 0

    app_seconds: int = 0
    website_seconds: int = 0

    worked_minutes: int = 0

    goals_total: int = 0
    goals_completed: int = 0

    goals_average_progress: float = 0.0


class AnalyticsAppsResponse(
    AnalyticsSchema
):
    workspace_id: uuid.UUID
    scope: str
    window: AnalyticsWindow

    total_intervals: int = 0
    total_seconds: int = 0

    top_apps: list[
        AnalyticsNamedUsage
    ] = Field(
        default_factory=list
    )


class AnalyticsWebsitesResponse(
    AnalyticsSchema
):
    workspace_id: uuid.UUID
    scope: str
    window: AnalyticsWindow

    total_intervals: int = 0
    total_seconds: int = 0

    top_websites: list[
        AnalyticsNamedUsage
    ] = Field(
        default_factory=list
    )


class AnalyticsGoalsResponse(
    AnalyticsSchema
):
    workspace_id: uuid.UUID
    scope: str
    window: AnalyticsWindow

    total: int = 0

    active: int = 0
    completed: int = 0
    cancelled: int = 0
    archived: int = 0

    average_progress: float = 0.0


class AnalyticsTrendSeries(
    AnalyticsSchema
):
    key: str

    points: list[
        AnalyticsSeriesPoint
    ] = Field(
        default_factory=list
    )


class AnalyticsTrendsResponse(
    AnalyticsSchema
):
    workspace_id: uuid.UUID
    scope: str
    window: AnalyticsWindow

    series: list[
        AnalyticsTrendSeries
    ] = Field(
        default_factory=list
    )


__all__ = [
    "AnalyticsWindow",
    "AnalyticsSeriesPoint",
    "AnalyticsNamedUsage",

    "AnalyticsOverviewResponse",
    "AnalyticsActivityResponse",
    "AnalyticsAttendanceResponse",
    "AnalyticsProductivityResponse",
    "AnalyticsAppsResponse",
    "AnalyticsWebsitesResponse",
    "AnalyticsGoalsResponse",
    "AnalyticsTrendSeries",
    "AnalyticsTrendsResponse",
]