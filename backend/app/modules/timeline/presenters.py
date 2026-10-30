from __future__ import annotations

from app.modules.timeline.enums import (
    TimelineEventType,
)


ATTENDANCE_EVENT_TYPE_MAP: dict[
    str,
    TimelineEventType,
] = {
    "check_in": (
        TimelineEventType
        .ATTENDANCE_CHECK_IN
    ),
    "check_out": (
        TimelineEventType
        .ATTENDANCE_CHECK_OUT
    ),
    "break_start": (
        TimelineEventType
        .ATTENDANCE_BREAK_START
    ),
    "break_end": (
        TimelineEventType
        .ATTENDANCE_BREAK_END
    ),
}


ATTENDANCE_TITLE_MAP: dict[
    str,
    str,
] = {
    "check_in": "Checked in",
    "check_out": "Checked out",
    "break_start": "Break started",
    "break_end": "Break ended",
}


def enum_string_value(
    value: object,
) -> str:
    raw_value = getattr(
        value,
        "value",
        value,
    )

    return str(
        raw_value
    )


def attendance_timeline_event_type(
    event_type: object,
) -> TimelineEventType:
    value = enum_string_value(
        event_type
    )

    try:
        return (
            ATTENDANCE_EVENT_TYPE_MAP[
                value
            ]
        )

    except KeyError as exc:
        raise ValueError(
            "Unsupported attendance "
            f"event type: {value}"
        ) from exc


def attendance_timeline_title(
    event_type: object,
) -> str:
    value = enum_string_value(
        event_type
    )

    try:
        return (
            ATTENDANCE_TITLE_MAP[
                value
            ]
        )

    except KeyError as exc:
        raise ValueError(
            "Unsupported attendance "
            f"event type: {value}"
        ) from exc


__all__ = [
    "ATTENDANCE_EVENT_TYPE_MAP",
    "ATTENDANCE_TITLE_MAP",
    "enum_string_value",
    "attendance_timeline_event_type",
    "attendance_timeline_title",
]