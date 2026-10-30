from __future__ import annotations

from enum import Enum


class MeetingStatus(
    str,
    Enum,
):
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MeetingType(
    str,
    Enum,
):
    VIDEO = "video"
    VOICE = "voice"
    IN_PERSON = "in_person"


class MeetingParticipantRole(
    str,
    Enum,
):
    ORGANIZER = "organizer"
    PARTICIPANT = "participant"


class MeetingParticipantStatus(
    str,
    Enum,
):
    INVITED = "invited"
    ACCEPTED = "accepted"
    DECLINED = "declined"


MEETING_STATUSES = tuple(
    item.value
    for item in MeetingStatus
)

MEETING_TYPES = tuple(
    item.value
    for item in MeetingType
)

MEETING_PARTICIPANT_ROLES = tuple(
    item.value
    for item in MeetingParticipantRole
)

MEETING_PARTICIPANT_STATUSES = tuple(
    item.value
    for item in MeetingParticipantStatus
)


__all__ = [
    "MeetingStatus",
    "MeetingType",
    "MeetingParticipantRole",
    "MeetingParticipantStatus",
    "MEETING_STATUSES",
    "MEETING_TYPES",
    "MEETING_PARTICIPANT_ROLES",
    "MEETING_PARTICIPANT_STATUSES",
]