from __future__ import annotations


MEETING_TABLE = "meetings"

MEETING_PARTICIPANT_TABLE = (
    "meeting_participants"
)


MEETING_REQUIRED_COLUMNS = frozenset(
    {
        "id",
        "title",
        "description",
        "meeting_type",
        "status",
        "scheduled_start_at",
        "scheduled_end_at",
        "started_at",
        "ended_at",
        "location",
        "created_by_user_id",
        "created_at",
        "updated_at",
    }
)


MEETING_PARTICIPANT_REQUIRED_COLUMNS = (
    frozenset(
        {
            "id",
            "meeting_id",
            "employee_id",
            "participant_role",
            "status",
            "created_at",
            "updated_at",
        }
    )
)


MEETING_STATUS_VALUES = frozenset(
    {
        "scheduled",
        "active",
        "completed",
        "cancelled",
    }
)


MEETING_TYPE_VALUES = frozenset(
    {
        "video",
        "voice",
        "in_person",
    }
)


MEETING_PARTICIPANT_ROLE_VALUES = (
    frozenset(
        {
            "organizer",
            "participant",
        }
    )
)


MEETING_PARTICIPANT_STATUS_VALUES = (
    frozenset(
        {
            "invited",
            "accepted",
            "declined",
        }
    )
)


__all__ = [
    "MEETING_TABLE",
    "MEETING_PARTICIPANT_TABLE",
    "MEETING_REQUIRED_COLUMNS",
    "MEETING_PARTICIPANT_REQUIRED_COLUMNS",
    "MEETING_STATUS_VALUES",
    "MEETING_TYPE_VALUES",
    "MEETING_PARTICIPANT_ROLE_VALUES",
    "MEETING_PARTICIPANT_STATUS_VALUES",
]