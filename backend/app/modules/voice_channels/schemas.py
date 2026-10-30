from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class VoiceSignalType(
    StrEnum
):
    OFFER = "offer"
    ANSWER = "answer"
    ICE_CANDIDATE = "ice_candidate"
    RENEGOTIATE = "renegotiate"


class VoicePresenceState(
    StrEnum
):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"


class VoiceSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True,
    )


class VoiceParticipantPublic(
    VoiceSchema
):
    id: uuid.UUID

    call_id: uuid.UUID

    user_id: uuid.UUID

    state: str

    self_muted: bool

    self_deafened: bool

    server_muted: bool

    server_deafened: bool

    effective_muted: bool

    effective_deafened: bool

    screen_sharing: bool

    presence: VoicePresenceState

    speaking: bool

    joined_at: datetime

    left_at: datetime | None


class VoiceParticipantListResponse(
    VoiceSchema
):
    call_id: uuid.UUID

    participants: list[
        VoiceParticipantPublic
    ] = Field(
        default_factory=list
    )


class VoiceCallPublic(
    VoiceSchema
):
    id: uuid.UUID

    channel_id: uuid.UUID

    created_by_user_id: uuid.UUID

    status: str

    created_at: datetime

    ended_at: datetime | None

    participants: list[
        VoiceParticipantPublic
    ] = Field(
        default_factory=list
    )


class VoiceJoinResponse(
    VoiceSchema
):
    call: VoiceCallPublic

    participant: VoiceParticipantPublic


class VoiceSelfStateRequest(
    VoiceSchema
):
    self_muted: bool | None = None

    self_deafened: bool | None = None


class VoiceModeratorStateRequest(
    VoiceSchema
):
    server_muted: bool | None = None

    server_deafened: bool | None = None


class VoiceModerationReasonRequest(
    VoiceSchema
):
    reason: str | None = Field(
        default=None,
        max_length=1000,
    )


class VoiceBanResponse(
    VoiceSchema
):
    channel_id: uuid.UUID

    user_id: uuid.UUID

    is_active: bool

    reason: str | None


class VoiceScreenShareResponse(
    VoiceSchema
):
    participant: VoiceParticipantPublic


class VoiceSignalRequest(
    VoiceSchema
):
    signal_type: VoiceSignalType

    target_user_id: uuid.UUID | None = None

    payload: dict[
        str,
        Any,
    ]


class VoiceSignalEnvelope(
    VoiceSchema
):
    event_id: uuid.UUID

    call_id: uuid.UUID

    channel_id: uuid.UUID

    sender_user_id: uuid.UUID

    target_user_id: uuid.UUID | None

    signal_type: VoiceSignalType

    payload: dict[
        str,
        Any,
    ]

    created_at: datetime


class VoiceSignalResponse(
    VoiceSchema
):
    event: VoiceSignalEnvelope


class VoiceSignalPollResponse(
    VoiceSchema
):
    events: list[
        VoiceSignalEnvelope
    ] = Field(
        default_factory=list
    )


class VoicePresenceHeartbeatRequest(
    VoiceSchema
):
    connection_id: str = Field(
        min_length=1,
        max_length=255,
    )


class VoiceSpeakingRequest(
    VoiceSchema
):
    speaking: bool


class VoiceRealtimeStateResponse(
    VoiceSchema
):
    call_id: uuid.UUID

    user_id: uuid.UUID

    presence: VoicePresenceState

    speaking: bool


class VoiceCapabilitiesResponse(
    VoiceSchema
):
    voice_channels: bool = True

    single_active_call_per_channel: bool = True

    self_mute: bool = True

    self_deafen: bool = True

    moderator_mute: bool = True

    moderator_deafen: bool = True

    kick: bool = True

    ban: bool = True

    screen_share: bool = True

    webrtc_signaling: bool = True

    presence: bool = True

    speaking_state: bool = True


__all__ = [
    "VoiceSignalType",
    "VoicePresenceState",
    "VoiceParticipantPublic",
    "VoiceParticipantListResponse",
    "VoiceCallPublic",
    "VoiceJoinResponse",
    "VoiceSelfStateRequest",
    "VoiceModeratorStateRequest",
    "VoiceModerationReasonRequest",
    "VoiceBanResponse",
    "VoiceScreenShareResponse",
    "VoiceSignalRequest",
    "VoiceSignalEnvelope",
    "VoiceSignalResponse",
    "VoiceSignalPollResponse",
    "VoicePresenceHeartbeatRequest",
    "VoiceSpeakingRequest",
    "VoiceRealtimeStateResponse",
    "VoiceCapabilitiesResponse",
]