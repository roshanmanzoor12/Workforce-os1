from __future__ import annotations

from app.modules.analytics.schemas import (
    AnalyticsProductivityResponse,
)


def test_analytics_productivity_contract():
    fields = (
        AnalyticsProductivityResponse
        .model_fields
    )

    required = {
        "workspace_id",
        "scope",
        "window",
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

    missing = (
        required
        - set(
            fields
        )
    )

    assert not missing, (
        "Analytics productivity "
        "contract is missing: "
        f"{sorted(missing)}"
    )


def test_analytics_productivity_has_no_score_field():
    fields = {
        field_name.lower()
        for field_name
        in (
            AnalyticsProductivityResponse
            .model_fields
        )
    }

    assert (
        "productivity_score"
        not in fields
    )

    assert (
        "employee_score"
        not in fields
    )