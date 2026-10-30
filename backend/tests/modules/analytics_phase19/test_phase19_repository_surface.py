from __future__ import annotations

from app.modules.analytics.repository import (
    AnalyticsRepository,
)


def test_repository_summary_sources_exist():
    required_methods = [
        "employee_count",
        "activity_summary",
        "attendance_summary",
        "app_summary",
        "website_summary",
        "goal_summary",
    ]

    for method_name in required_methods:
        assert hasattr(
            AnalyticsRepository,
            method_name,
        ), (
            "AnalyticsRepository "
            f"is missing {method_name}"
        )


def test_repository_daily_sources_exist():
    required_methods = [
        "activity_daily",
        "attendance_daily",
        "app_daily",
        "website_daily",
        "goals_daily",
    ]

    for method_name in required_methods:
        assert hasattr(
            AnalyticsRepository,
            method_name,
        ), (
            "AnalyticsRepository "
            f"is missing {method_name}"
        )