from __future__ import annotations

from enum import StrEnum


class TimelineEventType(StrEnum):
    GOAL_CREATED = "goal.created"

    NOTE_CREATED = "note.created"

    KNOWLEDGE_CREATED = (
        "knowledge.created"
    )

    MEETING_SCHEDULED = (
        "meeting.scheduled"
    )

    ATTENDANCE_CHECK_IN = (
        "attendance.check_in"
    )

    ATTENDANCE_CHECK_OUT = (
        "attendance.check_out"
    )

    ATTENDANCE_BREAK_START = (
        "attendance.break_start"
    )

    ATTENDANCE_BREAK_END = (
        "attendance.break_end"
    )

    SCREENSHOT_REQUESTED = (
        "screenshot.requested"
    )

    SCREENSHOT_COMPLETED = (
        "screenshot.completed"
    )

    SCREENSHOT_DENIED = (
        "screenshot.denied"
    )

    SCREENSHOT_EXPIRED = (
        "screenshot.expired"
    )

    SCREENSHOT_FAILED = (
        "screenshot.failed"
    )


class TimelineEntityType(StrEnum):
    GOAL = "goal"

    NOTE = "note"

    KNOWLEDGE = "knowledge"

    MEETING = "meeting"

    ATTENDANCE_EVENT = (
        "attendance_event"
    )

    SCREENSHOT_CAPTURE = (
        "screenshot_capture"
    )


class TimelineSourceKey(StrEnum):
    GOALS = "goals"

    NOTES = "notes"

    KNOWLEDGE = "knowledge"

    MEETINGS = "meetings"

    ATTENDANCE = "attendance"

    SCREENSHOTS = "screenshots"


__all__ = [
    "TimelineEventType",
    "TimelineEntityType",
    "TimelineSourceKey",
]