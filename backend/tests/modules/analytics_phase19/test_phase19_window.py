from __future__ import annotations

from datetime import (
    datetime,
    timedelta,
    timezone,
)

import pytest

from app.core.exceptions import (
    ValidationError,
)
from app.modules.analytics.service import (
    AnalyticsService,
)


def test_explicit_analytics_window():
    start_at = datetime(
        2026,
        1,
        1,
        tzinfo=timezone.utc,
    )

    end_at = datetime(
        2026,
        1,
        8,
        tzinfo=timezone.utc,
    )

    window = (
        AnalyticsService
        .resolve_window(
            start_at=start_at,
            end_at=end_at,
        )
    )

    assert (
        window.start_at
        == start_at
    )

    assert (
        window.end_at
        == end_at
    )


def test_naive_dates_are_normalized_to_utc():
    start_at = datetime(
        2026,
        1,
        1,
    )

    end_at = datetime(
        2026,
        1,
        2,
    )

    window = (
        AnalyticsService
        .resolve_window(
            start_at=start_at,
            end_at=end_at,
        )
    )

    assert (
        window.start_at.tzinfo
        is not None
    )

    assert (
        window.end_at.tzinfo
        is not None
    )


def test_invalid_reverse_window_rejected():
    now = datetime.now(
        timezone.utc
    )

    with pytest.raises(
        ValidationError
    ):
        (
            AnalyticsService
            .resolve_window(
                start_at=now,
                end_at=(
                    now
                    - timedelta(
                        minutes=1
                    )
                ),
            )
        )


def test_analytics_range_limit():
    start_at = datetime(
        2025,
        1,
        1,
        tzinfo=timezone.utc,
    )

    end_at = (
        start_at
        + timedelta(
            days=367
        )
    )

    with pytest.raises(
        ValidationError
    ):
        (
            AnalyticsService
            .resolve_window(
                start_at=start_at,
                end_at=end_at,
            )
        )


def test_max_range_constant():
    assert (
        AnalyticsService
        .MAX_RANGE_DAYS
        == 366
    )