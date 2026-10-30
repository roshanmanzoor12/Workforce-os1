from __future__ import annotations

from enum import Enum


class AttendanceStatus(
    str,
    Enum,
):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    HALF_DAY = "half_day"
    ON_LEAVE = "on_leave"
    HOLIDAY = "holiday"


class AttendanceEventType(
    str,
    Enum,
):
    CHECK_IN = "check_in"
    CHECK_OUT = "check_out"
    BREAK_START = "break_start"
    BREAK_END = "break_end"


class AttendanceSource(
    str,
    Enum,
):
    MANUAL = "manual"
    WEB = "web"
    DESKTOP_AGENT = "desktop_agent"
    IMPORT = "import"
    SYSTEM = "system"


ATTENDANCE_STATUSES = tuple(
    item.value
    for item in AttendanceStatus
)

ATTENDANCE_EVENT_TYPES = tuple(
    item.value
    for item in AttendanceEventType
)

ATTENDANCE_SOURCES = tuple(
    item.value
    for item in AttendanceSource
)


__all__ = [
    "AttendanceStatus",
    "AttendanceEventType",
    "AttendanceSource",
    "ATTENDANCE_STATUSES",
    "ATTENDANCE_EVENT_TYPES",
    "ATTENDANCE_SOURCES",
]