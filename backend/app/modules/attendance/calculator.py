from __future__ import annotations

from datetime import datetime

from app.modules.attendance.enums import (
    AttendanceEventType,
)
from app.modules.attendance.models import (
    AttendanceEvent,
)


class AttendanceCalculationError(
    ValueError
):
    pass


def calculate_attendance_totals(
    events: list[
        AttendanceEvent
    ],
) -> tuple[
    datetime | None,
    datetime | None,
    int,
    int,
]:
    ordered = sorted(
        events,
        key=lambda item: (
            item.occurred_at,
            item.created_at,
        ),
    )

    check_in_at: datetime | None = None
    check_out_at: datetime | None = None

    active_since: datetime | None = None
    break_since: datetime | None = None

    worked_seconds = 0
    break_seconds = 0

    for event in ordered:
        occurred_at = event.occurred_at

        if (
            event.event_type
            == AttendanceEventType.CHECK_IN.value
        ):
            if active_since is not None:
                raise AttendanceCalculationError(
                    "Duplicate check-in without check-out."
                )

            if break_since is not None:
                raise AttendanceCalculationError(
                    "Cannot check in during active break."
                )

            active_since = occurred_at

            if check_in_at is None:
                check_in_at = occurred_at

        elif (
            event.event_type
            == AttendanceEventType.BREAK_START.value
        ):
            if active_since is None:
                raise AttendanceCalculationError(
                    "Break cannot start before check-in."
                )

            if break_since is not None:
                raise AttendanceCalculationError(
                    "Break is already active."
                )

            worked_seconds += max(
                0,
                int(
                    (
                        occurred_at
                        - active_since
                    ).total_seconds()
                ),
            )

            active_since = None
            break_since = occurred_at

        elif (
            event.event_type
            == AttendanceEventType.BREAK_END.value
        ):
            if break_since is None:
                raise AttendanceCalculationError(
                    "Break end has no matching start."
                )

            break_seconds += max(
                0,
                int(
                    (
                        occurred_at
                        - break_since
                    ).total_seconds()
                ),
            )

            break_since = None
            active_since = occurred_at

        elif (
            event.event_type
            == AttendanceEventType.CHECK_OUT.value
        ):
            if break_since is not None:
                raise AttendanceCalculationError(
                    "End break before check-out."
                )

            if active_since is None:
                raise AttendanceCalculationError(
                    "Check-out has no active check-in."
                )

            worked_seconds += max(
                0,
                int(
                    (
                        occurred_at
                        - active_since
                    ).total_seconds()
                ),
            )

            active_since = None
            check_out_at = occurred_at

        else:
            raise AttendanceCalculationError(
                "Unknown attendance event type."
            )

    worked_minutes = (
        worked_seconds // 60
    )

    break_minutes = (
        break_seconds // 60
    )

    return (
        check_in_at,
        check_out_at,
        worked_minutes,
        break_minutes,
    )


__all__ = [
    "AttendanceCalculationError",
    "calculate_attendance_totals",
]