from __future__ import annotations

import inspect

from app.modules.analytics.service import (
    AnalyticsService,
)


def test_overview_uses_domain_summaries():
    source = inspect.getsource(
        AnalyticsService.overview
    )

    required_calls = [
        "employee_count",
        "activity_summary",
        "attendance_summary",
        "app_summary",
        "website_summary",
        "goal_summary",
    ]

    for method_name in required_calls:
        assert (
            method_name
            in source
        )


def test_productivity_uses_observed_domains():
    source = inspect.getsource(
        AnalyticsService.productivity
    )

    required_calls = [
        "activity_summary",
        "attendance_summary",
        "app_summary",
        "website_summary",
        "goal_summary",
    ]

    for method_name in required_calls:
        assert (
            method_name
            in source
        )


def test_apps_use_repository_data():
    source = inspect.getsource(
        AnalyticsService.apps
    )

    assert (
        "app_summary"
        in source
    )


def test_websites_use_repository_data():
    source = inspect.getsource(
        AnalyticsService.websites
    )

    assert (
        "website_summary"
        in source
    )


def test_goals_use_repository_data():
    source = inspect.getsource(
        AnalyticsService.goals
    )

    assert (
        "goal_summary"
        in source
    )