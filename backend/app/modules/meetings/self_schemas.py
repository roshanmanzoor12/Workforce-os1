from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from app.modules.meetings.enums import (
    MeetingParticipantStatus,
    MeetingStatus,
    MeetingType,
)


class MeetingSelfSchema(
    BaseModel
):
    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )


class MeetingInvitationPublic(
    MeetingSelfSchema
):
    meeting_id: uuid.UUID

    title: str

    meeting_type: MeetingType
    meeting_status: MeetingStatus

    scheduled_start_at: datetime
    scheduled_end_at: datetime | None

    participant_status: (
        MeetingParticipantStatus
    )


class MeetingInvitationListResponse(
    MeetingSelfSchema
):
    invitations: list[
        MeetingInvitationPublic
    ] = Field(
        default_factory=list
    )

    total: int = Field(
        ge=0,
    )


class MeetingSelfResponseRequest(
    MeetingSelfSchema
):
    status: MeetingParticipantStatus


class MeetingSelfResponseResult(
    MeetingSelfSchema
):
    meeting_id: uuid.UUID
    employee_id: uuid.UUID
    status: MeetingParticipantStatus


class MeetingSelfResponse(
    MeetingSelfSchema
):
    message: str

    participant: (
        MeetingSelfResponseResult
    )


__all__ = [
    "MeetingInvitationPublic",
    "MeetingInvitationListResponse",
    "MeetingSelfResponseRequest",
    "MeetingSelfResponseResult",
    "MeetingSelfResponse",
]