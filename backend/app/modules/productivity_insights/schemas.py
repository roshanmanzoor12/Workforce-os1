from __future__ import annotations

import uuid

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from app.modules.analytics.schemas import (
    AnalyticsNamedUsage,
    AnalyticsWindow,
)


class ProductivityInsightsSchema(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True,
    )


class ProductivityOverviewResponse(
    ProductivityInsightsSchema
):
    workspace_id: uuid.UUID

    scope: str

    window: AnalyticsWindow

    employee_count: int = 0

    activity_events: int = 0
    active_events: int = 0
    idle_events: int = 0

    active_event_percent: float = 0.0
    idle_event_percent: float = 0.0

    average_idle_seconds: float = 0.0

    worked_minutes: int = 0
    break_minutes: int = 0

    app_seconds: int = 0
    website_seconds: int = 0

    goals_total: int = 0
    goals_completed: int = 0

    goal_completion_percent: float = 0.0
    goals_average_progress: float = 0.0


class ProductivityActivityResponse(
    ProductivityInsightsSchema
):
    workspace_id: uuid.UUID

    scope: str

    window: AnalyticsWindow

    activity_events: int = 0

    active_events: int = 0
    idle_events: int = 0

    active_event_percent: float = 0.0
    idle_event_percent: float = 0.0

    average_idle_seconds: float = 0.0

    attendance_records: int = 0

    worked_minutes: int = 0
    break_minutes: int = 0


class ProductivityUsageResponse(
    ProductivityInsightsSchema
):
    workspace_id: uuid.UUID

    scope: str

    window: AnalyticsWindow

    app_intervals: int = 0
    app_seconds: int = 0

    website_intervals: int = 0
    website_seconds: int = 0

    top_apps: list[
        AnalyticsNamedUsage
    ] = Field(
        default_factory=list
    )

    top_websites: list[
        AnalyticsNamedUsage
    ] = Field(
        default_factory=list
    )


class ProductivityGoalsResponse(
    ProductivityInsightsSchema
):
    workspace_id: uuid.UUID

    scope: str

    window: AnalyticsWindow

    total: int = 0

    active: int = 0
    completed: int = 0
    cancelled: int = 0
    archived: int = 0

    completion_percent: float = 0.0
    average_progress: float = 0.0


class ProductivityMetricComparison(
    ProductivityInsightsSchema
):
    key: str

    current: float

    previous: float

    absolute_change: float

    percent_change: (
        float | None
    ) = None


class ProductivityComparisonResponse(
    ProductivityInsightsSchema
):
    workspace_id: uuid.UUID

    scope: str

    current_window: AnalyticsWindow
    previous_window: AnalyticsWindow

    metrics: list[
        ProductivityMetricComparison
    ] = Field(
        default_factory=list
    )


__all__ = [
    "ProductivityOverviewResponse",
    "ProductivityActivityResponse",
    "ProductivityUsageResponse",
    "ProductivityGoalsResponse",
    "ProductivityMetricComparison",
    "ProductivityComparisonResponse",
]