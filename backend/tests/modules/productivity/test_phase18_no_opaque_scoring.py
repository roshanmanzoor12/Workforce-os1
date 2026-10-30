from __future__ import annotations

from app.modules.analytics.schemas import (
    AnalyticsProductivityResponse,
)
from app.modules.productivity_insights.schemas import (
    ProductivityActivityResponse,
    ProductivityComparisonResponse,
    ProductivityGoalsResponse,
    ProductivityOverviewResponse,
    ProductivityUsageResponse,
)


def _assert_no_opaque_score(
    schema,
) -> None:
    forbidden = {
        "productivity_score",
        "performance_score",
        "employee_score",
        "risk_score",
    }

    fields = {
        field_name.lower()
        for field_name
        in schema.model_fields
    }

    assert not (
        fields
        & forbidden
    ), (
        f"{schema.__name__} exposes "
        "an opaque employee score."
    )


def test_productivity_schemas_do_not_expose_opaque_scores():
    schemas = [
        ProductivityOverviewResponse,
        ProductivityActivityResponse,
        ProductivityUsageResponse,
        ProductivityGoalsResponse,
        ProductivityComparisonResponse,
        AnalyticsProductivityResponse,
    ]

    for schema in schemas:
        _assert_no_opaque_score(
            schema
        )