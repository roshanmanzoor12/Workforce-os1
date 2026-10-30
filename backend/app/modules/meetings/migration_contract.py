from __future__ import annotations


MEETINGS_TENANT_REVISION = (
    "d3e4f5a6b7c8"
)

MEETINGS_TENANT_DOWN_REVISION = (
    "c2d3e4f5a6b7"
)

MEETINGS_TENANT_TABLES = frozenset(
    {
        "meetings",
        "meeting_participants",
    }
)


MEETINGS_REQUIRED_INDEXES = frozenset(
    {
        "ix_meetings_status",
        "ix_meetings_start",
        "ix_meetings_created_by_user",
        "ix_meeting_participants_meeting",
        "ix_meeting_participants_employee",
    }
)


__all__ = [
    "MEETINGS_TENANT_REVISION",
    "MEETINGS_TENANT_DOWN_REVISION",
    "MEETINGS_TENANT_TABLES",
    "MEETINGS_REQUIRED_INDEXES",
]