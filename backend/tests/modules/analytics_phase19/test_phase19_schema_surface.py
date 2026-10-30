from __future__ import annotations

from app.modules.analytics.schemas import (
    AnalyticsActivityResponse,
    AnalyticsAppsResponse,
    AnalyticsAttendanceResponse,
    AnalyticsGoalsResponse,
    AnalyticsNamedUsage,
    AnalyticsOverviewResponse,
    AnalyticsProductivityResponse,
    AnalyticsSeriesPoint,
    AnalyticsTrendsResponse,
    AnalyticsTrendSeries,
    AnalyticsWebsitesResponse,
    AnalyticsWindow,
)


def fields(
    schema,
) -> set[str]:
    return set(
        schema.model_fields
    )


def test_common_workspace_scope_contract():
    response_types = [
        AnalyticsOverviewResponse,
        AnalyticsActivityResponse,
        AnalyticsAttendanceResponse,
        AnalyticsProductivityResponse,
        AnalyticsAppsResponse,
        AnalyticsWebsitesResponse,
        AnalyticsGoalsResponse,
        AnalyticsTrendsResponse,
    ]

    for response_type in response_types:
        schema_fields = fields(
            response_type
        )

        assert (
            "workspace_id"
            in schema_fields
        )

        assert (
            "scope"
            in schema_fields
        )

        assert (
            "window"
            in schema_fields
        )


def test_analytics_window_contract():
    assert fields(
        AnalyticsWindow
    ) == {
        "start_at",
        "end_at",
    }


def test_activity_schema_contract():
    required = {
        "total_events",
        "active_events",
        "idle_events",
        "average_idle_seconds",
        "daily",
    }

    assert required.issubset(
        fields(
            AnalyticsActivityResponse
        )
    )


def test_attendance_schema_contract():
    required = {
        "total_records",
        "worked_minutes",
        "break_minutes",
        "status_breakdown",
        "daily",
    }

    assert required.issubset(
        fields(
            AnalyticsAttendanceResponse
        )
    )


def test_productivity_schema_contract():
    required = {
        "activity_events",
        "active_events",
        "idle_events",
        "app_seconds",
        "website_seconds",
        "worked_minutes",
        "goals_total",
        "goals_completed",
        "goals_average_progress",
    }

    assert required.issubset(
        fields(
            AnalyticsProductivityResponse
        )
    )


def test_usage_contracts():
    assert {
        "total_intervals",
        "total_seconds",
        "top_apps",
    }.issubset(
        fields(
            AnalyticsAppsResponse
        )
    )

    assert {
        "total_intervals",
        "total_seconds",
        "top_websites",
    }.issubset(
        fields(
            AnalyticsWebsitesResponse
        )
    )

    assert {
        "name",
        "duration_seconds",
        "event_count",
    }.issubset(
        fields(
            AnalyticsNamedUsage
        )
    )


def test_goal_contract():
    required = {
        "total",
        "active",
        "completed",
        "cancelled",
        "archived",
        "average_progress",
    }

    assert required.issubset(
        fields(
            AnalyticsGoalsResponse
        )
    )


def test_trend_contract():
    assert {
        "date",
        "value",
    }.issubset(
        fields(
            AnalyticsSeriesPoint
        )
    )

    assert {
        "key",
        "points",
    }.issubset(
        fields(
            AnalyticsTrendSeries
        )
    )

    assert (
        "series"
        in fields(
            AnalyticsTrendsResponse
        )
    )