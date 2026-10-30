from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.modules.meetings.enums import (
    MeetingParticipantRole,
    MeetingParticipantStatus,
    MeetingStatus,
    MeetingType,
)


class MeetingSchemaBase(
    BaseModel
):
    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )


class MeetingCreateRequest(
    MeetingSchemaBase
):
    title: str = Field(
        min_length=1,
        max_length=200,
    )

    description: str | None = Field(
        default=None,
        max_length=5000,
    )

    meeting_type: MeetingType = (
        MeetingType.VIDEO
    )

    scheduled_start_at: datetime

    scheduled_end_at: (
        datetime | None
    ) = None

    location: str | None = Field(
        default=None,
        max_length=500,
    )

    participant_employee_ids: list[
        uuid.UUID
    ] = Field(
        default_factory=list,
        max_length=500,
    )

    @field_validator(
        "title",
        "description",
        "location",
        mode="before",
    )
    @classmethod
    def normalize_strings(
        cls,
        value,
    ):
        if value is None:
            return None

        if not isinstance(
            value,
            str,
        ):
            return value

        value = value.strip()

        return value or None

    @model_validator(
        mode="after",
    )
    def validate_schedule(
        self,
    ) -> "MeetingCreateRequest":
        if (
            self.scheduled_end_at
            is not None
            and self.scheduled_end_at
            <= self.scheduled_start_at
        ):
            raise ValueError(
                "scheduled_end_at must be "
                "after scheduled_start_at."
            )

        return self


class MeetingUpdateRequest(
    MeetingSchemaBase
):
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )

    description: str | None = Field(
        default=None,
        max_length=5000,
    )

    meeting_type: (
        MeetingType | None
    ) = None

    scheduled_start_at: (
        datetime | None
    ) = None

    scheduled_end_at: (
        datetime | None
    ) = None

    location: str | None = Field(
        default=None,
        max_length=500,
    )

    @field_validator(
        "title",
        "description",
        "location",
        mode="before",
    )
    @classmethod
    def normalize_strings(
        cls,
        value,
    ):
        if value is None:
            return None

        if not isinstance(
            value,
            str,
        ):
            return value

        value = value.strip()

        return value or None


class MeetingParticipantAddRequest(
    MeetingSchemaBase
):
    employee_id: uuid.UUID

    participant_role: (
        MeetingParticipantRole
    ) = (
        MeetingParticipantRole
        .PARTICIPANT
    )


class MeetingParticipantStatusRequest(
    MeetingSchemaBase
):
    status: MeetingParticipantStatus


class MeetingParticipantPublic(
    MeetingSchemaBase
):
    id: uuid.UUID

    meeting_id: uuid.UUID
    employee_id: uuid.UUID

    participant_role: (
        MeetingParticipantRole
    )

    status: (
        MeetingParticipantStatus
    )

    created_at: datetime
    updated_at: datetime


class MeetingPublic(
    MeetingSchemaBase
):
    id: uuid.UUID

    title: str
    description: str | None

    meeting_type: MeetingType
    status: MeetingStatus

    scheduled_start_at: datetime
    scheduled_end_at: datetime | None

    started_at: datetime | None
    ended_at: datetime | None

    location: str | None

    created_by_user_id: uuid.UUID

    created_at: datetime
    updated_at: datetime


class MeetingDetailResponse(
    MeetingSchemaBase
):
    meeting: MeetingPublic

    participants: list[
        MeetingParticipantPublic
    ] = Field(
        default_factory=list
    )


class MeetingResponse(
    MeetingSchemaBase
):
    message: str
    meeting: MeetingPublic


class MeetingListResponse(
    MeetingSchemaBase
):
    meetings: list[
        MeetingPublic
    ] = Field(
        default_factory=list
    )

    total: int = Field(
        ge=0,
    )


class MeetingParticipantResponse(
    MeetingSchemaBase
):
    message: str

    participant: (
        MeetingParticipantPublic
    )


__all__ = [
    "MeetingCreateRequest",
    "MeetingUpdateRequest",
    "MeetingParticipantAddRequest",
    "MeetingParticipantStatusRequest",
    "MeetingParticipantPublic",
    "MeetingPublic",
    "MeetingDetailResponse",
    "MeetingResponse",
    "MeetingListResponse",
    "MeetingParticipantResponse",
]