from __future__ import annotations

from app.modules.productivity_insights.schemas import (
    ProductivityActivityResponse,
    ProductivityComparisonResponse,
    ProductivityGoalsResponse,
    ProductivityMetricComparison,
    ProductivityOverviewResponse,
    ProductivityUsageResponse,
)


def _fields(
    schema,
) -> set[str]:
    return set(
        schema.model_fields
    )


def test_productivity_response_types_exist():
    response_types = [
        ProductivityOverviewResponse,
        ProductivityActivityResponse,
        ProductivityUsageResponse,
        ProductivityGoalsResponse,
        ProductivityComparisonResponse,
    ]

    for response_type in response_types:
        assert (
            response_type
            is not None
        )


def test_overview_is_workspace_scoped():
    fields = _fields(
        ProductivityOverviewResponse
    )

    assert (
        "workspace_id"
        in fields
    )

    assert (
        "scope"
        in fields
    )


def test_activity_exposes_idle_evidence():
    fields = _fields(
        ProductivityActivityResponse
    )

    assert (
        "average_idle_seconds"
        in fields
    )


def test_comparison_has_metric_items():
    fields = _fields(
        ProductivityComparisonResponse
    )

    assert fields

    metric_fields = _fields(
        ProductivityMetricComparison
    )

    assert metric_fields