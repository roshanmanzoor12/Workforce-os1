from __future__ import annotations

from dataclasses import dataclass


@dataclass(
    frozen=True,
    slots=True,
)
class MetricChange:
    current: float
    previous: float
    absolute_change: float
    percent_change: float | None


def percentage(
    numerator: float | int,
    denominator: float | int,
) -> float:
    if denominator <= 0:
        return 0.0

    return round(
        (
            float(
                numerator
            )
            / float(
                denominator
            )
        )
        * 100.0,
        2,
    )


def metric_change(
    *,
    current: float | int,
    previous: float | int,
) -> MetricChange:
    current_value = float(
        current
    )

    previous_value = float(
        previous
    )

    absolute = (
        current_value
        - previous_value
    )

    percent: float | None

    if previous_value == 0:
        percent = None

    else:
        percent = round(
            (
                absolute
                / abs(
                    previous_value
                )
            )
            * 100.0,
            2,
        )

    return MetricChange(
        current=current_value,
        previous=previous_value,
        absolute_change=round(
            absolute,
            2,
        ),
        percent_change=percent,
    )


__all__ = [
    "MetricChange",
    "percentage",
    "metric_change",
]