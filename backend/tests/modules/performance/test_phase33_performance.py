from datetime import date
from uuid import uuid4

import pytest

from app.modules.performance.models import (
    PerformanceReview,
    PerformanceReviewCycle,
)
from app.modules.performance.router import router
from app.modules.performance.schemas import (
    ReviewCreate,
    ReviewCycleCreate,
)


def test_performance_routes_exist() -> None:
    paths = {
        route.path
        for route in router.routes
    }

    assert (
        "/workspaces/{workspace_id}/performance/cycles"
        in paths
    )
    assert (
        "/workspaces/{workspace_id}/performance/reviews"
        in paths
    )


def test_performance_table_names() -> None:
    assert (
        PerformanceReviewCycle.__tablename__
        == "performance_review_cycles"
    )
    assert (
        PerformanceReview.__tablename__
        == "performance_reviews"
    )


def test_valid_review_cycle() -> None:
    cycle = ReviewCycleCreate(
        name="Annual Review 2026",
        starts_on=date(2026, 1, 1),
        ends_on=date(2026, 12, 31),
    )

    assert cycle.name == "Annual Review 2026"


def test_invalid_review_cycle_dates() -> None:
    with pytest.raises(ValueError):
        ReviewCycleCreate(
            name="Invalid Review",
            starts_on=date(2026, 12, 31),
            ends_on=date(2026, 1, 1),
        )


def test_valid_review() -> None:
    review = ReviewCreate(
        cycle_id=uuid4(),
        employee_id=uuid4(),
        rating=4,
        summary="Good performance.",
    )

    assert review.rating == 4
    assert review.summary == "Good performance."