from __future__ import annotations

from types import SimpleNamespace

from app.modules.leave.calendar_service import (
    LeaveCalendarService,
)


def schedule_day(
    *,
    working: bool,
    holiday: bool = False,
):
    return SimpleNamespace(
        is_working_day=working,
        is_holiday=holiday,
    )


def test_working_day_is_chargeable():
    assert (
        LeaveCalendarService
        .is_chargeable_schedule_day(
            schedule_day(
                working=True,
            )
        )
        is True
    )


def test_non_working_day_not_chargeable():
    assert (
        LeaveCalendarService
        .is_chargeable_schedule_day(
            schedule_day(
                working=False,
            )
        )
        is False
    )


def test_holiday_not_chargeable():
    assert (
        LeaveCalendarService
        .is_chargeable_schedule_day(
            schedule_day(
                working=True,
                holiday=True,
            )
        )
        is False
    )


def test_missing_schedule_fields_safe():
    assert (
        LeaveCalendarService
        .is_chargeable_schedule_day(
            SimpleNamespace()
        )
        is False
    )