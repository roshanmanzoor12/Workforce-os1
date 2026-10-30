from __future__ import annotations

import inspect

from app.modules.analytics.router import (
    analytics_activity,
    analytics_apps,
    analytics_attendance,
    analytics_goals,
    analytics_overview,
    analytics_productivity,
    analytics_trends,
    analytics_websites,
)
from app.modules.analytics.schemas import (
    AnalyticsActivityResponse,
    AnalyticsAppsResponse,
    AnalyticsAttendanceResponse,
    AnalyticsGoalsResponse,
    AnalyticsOverviewResponse,
    AnalyticsProductivityResponse,
    AnalyticsTrendsResponse,
    AnalyticsWebsitesResponse,
)


ROUTE_FUNCTIONS = [
    analytics_overview,
    analytics_activity,
    analytics_attendance,
    analytics_productivity,
    analytics_apps,
    analytics_websites,
    analytics_goals,
    analytics_trends,
]


SCHEMAS = [
    AnalyticsOverviewResponse,
    AnalyticsActivityResponse,
    AnalyticsAttendanceResponse,
    AnalyticsProductivityResponse,
    AnalyticsAppsResponse,
    AnalyticsWebsitesResponse,
    AnalyticsGoalsResponse,
    AnalyticsTrendsResponse,
]


def test_every_route_resolves_access():
    for function in ROUTE_FUNCTIONS:
        source = inspect.getsource(
            function
        )

        assert (
            "_access("
            in source
        ), (
            f"{function.__name__} "
            "does not resolve "
            "analytics access."
        )


def test_every_route_uses_workspace_id():
    for function in ROUTE_FUNCTIONS:
        source = inspect.getsource(
            function
        )

        assert (
            "workspace_id"
            in source
        )


def test_no_opaque_employee_score_fields():
    forbidden = {
        "employee_score",
        "performance_score",
        "risk_score",
        "productivity_score",
    }

    for schema in SCHEMAS:
        actual = {
            field.lower()
            for field
            in schema.model_fields
        }

        assert not (
            actual
            & forbidden
        ), (
            f"{schema.__name__} "
            "contains opaque scoring."
        )


def test_no_raw_tenant_database_identifier():
    for schema in SCHEMAS:
        fields = {
            field.lower()
            for field
            in schema.model_fields
        }

        forbidden = {
            "tenant_database",
            "database_name",
            "database_url",
            "tenant_db",
        }

        assert not (
            fields
            & forbidden
        )