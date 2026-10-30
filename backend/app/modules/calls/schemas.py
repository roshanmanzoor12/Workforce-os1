from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

from app.modules.calls.enums import (
    CallKind,
    CallParticipantState,
    CallScope,
    CallSignalType,
    CallStatus,
    ScreenShareState,
)


class CreateCallRequest(BaseModel):
    scope: CallScope
    kind: CallKind

    conversation_id: (
        uuid.UUID | None
    ) = None

    channel_id: (
        uuid.UUID | None
    ) = None

    invited_user_ids: list[
        uuid.UUID
    ] = Field(
        default_factory=list,
        max_length=99,
    )

    @model_validator(
        mode="after"
    )
    def validate_target(
        self,
    ):
        if (
            self.scope
            == CallScope.CONVERSATION
        ):
            if (
                self.conversation_id
                is None
            ):
                raise ValueError(
                    "conversation_id is required."
                )

            if self.channel_id is not None:
                raise ValueError(
                    "channel_id must be empty."
                )

        if self.scope == CallScope.CHANNEL:
            if self.channel_id is None:
                raise ValueError(
                    "channel_id is required."
                )

            if (
                self.conversation_id
                is not None
            ):
                raise ValueError(
                    "conversation_id must be empty."
                )

        return self


class CallParticipantResponse(
    BaseModel
):
    model_config = ConfigDict(
        from_attributes=True
    )

    user_id: uuid.UUID
    state: CallParticipantState

    microphone_enabled: bool
    camera_enabled: bool

    screen_share_state: (
        ScreenShareState
    )

    joined_at: datetime | None
    left_at: datetime | None


class CallResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: uuid.UUID

    scope: CallScope
    conversation_id: uuid.UUID | None
    channel_id: uuid.UUID | None

    started_by_user_id: uuid.UUID

    kind: CallKind
    status: CallStatus

    created_at: datetime
    started_at: datetime | None
    ended_at: datetime | None

    participants: list[
        CallParticipantResponse
    ] = Field(
        default_factory=list
    )


class CallMediaStateRequest(BaseModel):
    microphone_enabled: (
        bool | None
    ) = None

    camera_enabled: (
        bool | None
    ) = None


class CallHeartbeatRequest(BaseModel):
    connection_id: str = Field(
        min_length=1,
        max_length=255,
    )


class CallHeartbeatResponse(BaseModel):
    call_id: uuid.UUID
    user_id: uuid.UUID
    alive: bool = True
    timestamp: datetime


class CallSignalRequest(BaseModel):
    signal_type: CallSignalType

    target_user_id: (
        uuid.UUID | None
    ) = None

    payload: dict[str, object]


class CallSignalResponse(BaseModel):
    event: dict[str, object]


class CallParticipantsResponse(
    BaseModel
):
    call_id: uuid.UUID

    participants: list[
        CallParticipantResponse
    ]