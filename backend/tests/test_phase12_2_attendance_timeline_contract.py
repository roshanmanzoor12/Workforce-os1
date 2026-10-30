from __future__ import annotations

from app.modules.timeline.enums import (
    TimelineEntityType,
    TimelineEventType,
    TimelineSourceKey,
)
from app.modules.timeline.presenters import (
    attendance_timeline_event_type,
    attendance_timeline_title,
)


def test_attendance_source_key() -> None:
    assert (
        TimelineSourceKey
        .ATTENDANCE
        .value
        == "attendance"
    )


def test_attendance_entity_type() -> None:
    assert (
        TimelineEntityType
        .ATTENDANCE_EVENT
        .value
        == "attendance_event"
    )


def test_attendance_event_types() -> None:
    expected = {
        "attendance.check_in",
        "attendance.check_out",
        "attendance.break_start",
        "attendance.break_end",
    }

    actual = {
        item.value
        for item
        in TimelineEventType
        if item.value.startswith(
            "attendance."
        )
    }

    assert actual == expected


def test_check_in_mapping() -> None:
    assert (
        attendance_timeline_event_type(
            "check_in"
        )
        == (
            TimelineEventType
            .ATTENDANCE_CHECK_IN
        )
    )


def test_check_out_mapping() -> None:
    assert (
        attendance_timeline_event_type(
            "check_out"
        )
        == (
            TimelineEventType
            .ATTENDANCE_CHECK_OUT
        )
    )


def test_break_start_mapping() -> None:
    assert (
        attendance_timeline_event_type(
            "break_start"
        )
        == (
            TimelineEventType
            .ATTENDANCE_BREAK_START
        )
    )


def test_break_end_mapping() -> None:
    assert (
        attendance_timeline_event_type(
            "break_end"
        )
        == (
            TimelineEventType
            .ATTENDANCE_BREAK_END
        )
    )


def test_attendance_titles() -> None:
    assert (
        attendance_timeline_title(
            "check_in"
        )
        == "Checked in"
    )

    assert (
        attendance_timeline_title(
            "check_out"
        )
        == "Checked out"
    )

    assert (
        attendance_timeline_title(
            "break_start"
        )
        == "Break started"
    )

    assert (
        attendance_timeline_title(
            "break_end"
        )
        == "Break ended"
    )