from __future__ import annotations

from collections.abc import Iterable


ABSENCE_STATUSES = frozenset(
    {
        "absent",
        "absence",
        "missed",
    }
)


ACTIVE_GOAL_STATUSES = frozenset(
    {
        "active",
    }
)


COMPLETED_GOAL_STATUSES = frozenset(
    {
        "completed",
    }
)


CANCELLED_GOAL_STATUSES = frozenset(
    {
        "cancelled",
        "canceled",
    }
)


ARCHIVED_GOAL_STATUSES = frozenset(
    {
        "archived",
    }
)


def normalized_status(
    value: str | None,
) -> str:
    if value is None:
        return ""

    return (
        value
        .strip()
        .casefold()
    )


def is_absence_status(
    value: str | None,
) -> bool:
    return (
        normalized_status(
            value
        )
        in ABSENCE_STATUSES
    )


def safe_average(
    values: Iterable[
        int | float | None
    ],
) -> float:
    items = [
        float(value)
        for value in values
        if value is not None
    ]

    if not items:
        return 0.0

    return round(
        sum(items)
        / len(items),
        2,
    )


def safe_ratio_average(
    *,
    total: int | float,
    count: int,
) -> float:
    if count <= 0:
        return 0.0

    return round(
        float(total)
        / float(count),
        2,
    )


def clamp_percent(
    value: int | float | None,
) -> float:
    if value is None:
        return 0.0

    return round(
        min(
            100.0,
            max(
                0.0,
                float(value),
            ),
        ),
        2,
    )


__all__ = [
    "ABSENCE_STATUSES",
    "ACTIVE_GOAL_STATUSES",
    "COMPLETED_GOAL_STATUSES",
    "CANCELLED_GOAL_STATUSES",
    "ARCHIVED_GOAL_STATUSES",
    "normalized_status",
    "is_absence_status",
    "safe_average",
    "safe_ratio_average",
    "clamp_percent",
]