from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# =========================================================
# ENUMS
# =========================================================


class WorkspaceChannelRealtimeEventType(StrEnum):
    CONNECTED = "channel.connected"
    DISCONNECTED = "channel.disconnected"

    MESSAGE_CREATED = "message.created"
    MESSAGE_UPDATED = "message.updated"
    MESSAGE_DELETED = "message.deleted"

    ATTACHMENT_BOUND = "channel.attachment.bound"

    TYPING_STARTED = "channel.typing.started"
    TYPING_STOPPED = "channel.typing.stopped"
    PRESENCE_UPDATED = "channel.presence.updated"

    CHANNEL_CREATED = "channel.created"
    CHANNEL_UPDATED = "channel.updated"
    CHANNEL_ARCHIVED = "channel.archived"

    HEARTBEAT = "channel.heartbeat"


class WorkspaceChannelPresenceState(StrEnum):
    ONLINE = "online"
    IDLE = "idle"
    OFFLINE = "offline"


# =========================================================
# BASE
# =========================================================


class WorkspaceChannelRealtimeSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


# =========================================================
# WEBSOCKET TICKET
# =========================================================


class WorkspaceChannelRealtimeTicketResponse(
    WorkspaceChannelRealtimeSchema
):
    ticket: str = Field(min_length=20)
    expires_in_seconds: int = Field(gt=0)


# =========================================================
# CHANNEL SUBSCRIPTION
# =========================================================


class WorkspaceChannelSubscribeRequest(
    WorkspaceChannelRealtimeSchema
):
    channel_id: uuid.UUID


class WorkspaceChannelUnsubscribeRequest(
    WorkspaceChannelRealtimeSchema
):
    channel_id: uuid.UUID


# =========================================================
# TYPING
# =========================================================


class WorkspaceChannelTypingRequest(
    WorkspaceChannelRealtimeSchema
):
    channel_id: uuid.UUID


class WorkspaceChannelTypingUser(
    WorkspaceChannelRealtimeSchema
):
    user_id: uuid.UUID
    channel_id: uuid.UUID
    started_at: datetime


class WorkspaceChannelTypingUsersResponse(
    WorkspaceChannelRealtimeSchema
):
    channel_id: uuid.UUID
    users: list[WorkspaceChannelTypingUser] = Field(
        default_factory=list
    )


# =========================================================
# PRESENCE
# =========================================================


class WorkspaceChannelPresenceUpdateRequest(
    WorkspaceChannelRealtimeSchema
):
    status: WorkspaceChannelPresenceState


class WorkspaceChannelPresencePublic(
    WorkspaceChannelRealtimeSchema
):
    user_id: uuid.UUID
    status: WorkspaceChannelPresenceState
    last_seen_at: datetime


class WorkspaceChannelPresenceListResponse(
    WorkspaceChannelRealtimeSchema
):
    workspace_id: uuid.UUID
    items: list[WorkspaceChannelPresencePublic] = Field(
        default_factory=list
    )


# =========================================================
# HEARTBEAT
# =========================================================


class WorkspaceChannelHeartbeatResponse(
    WorkspaceChannelRealtimeSchema
):
    success: bool = True
    workspace_id: uuid.UUID
    actor_user_id: uuid.UUID
    timestamp: datetime


# =========================================================
# EVENT PAYLOADS
# =========================================================


class WorkspaceChannelMessageEventPayload(
    WorkspaceChannelRealtimeSchema
):
    message_id: uuid.UUID
    channel_id: uuid.UUID
    sender_user_id: uuid.UUID | None = None
    message_type: str
    content: str
    edited_at: datetime | None = None
    deleted_at: datetime | None = None
    created_at: datetime


class WorkspaceChannelAttachmentEventPayload(
    WorkspaceChannelRealtimeSchema
):
    message_id: uuid.UUID
    channel_id: uuid.UUID
    attachment_ids: list[uuid.UUID] = Field(
        default_factory=list
    )


class WorkspaceChannelTypingEventPayload(
    WorkspaceChannelRealtimeSchema
):
    channel_id: uuid.UUID
    user_id: uuid.UUID
    typing: bool


class WorkspaceChannelPresenceEventPayload(
    WorkspaceChannelRealtimeSchema
):
    user_id: uuid.UUID
    status: WorkspaceChannelPresenceState
    last_seen_at: datetime


class WorkspaceChannelLifecycleEventPayload(
    WorkspaceChannelRealtimeSchema
):
    channel_id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    channel_type: str
    is_active: bool


# =========================================================
# GENERIC EVENT ENVELOPE
# =========================================================


class WorkspaceChannelRealtimeEvent(
    WorkspaceChannelRealtimeSchema
):
    event_id: uuid.UUID
    event_type: WorkspaceChannelRealtimeEventType
    workspace_id: uuid.UUID
    channel_id: uuid.UUID | None = None
    actor_user_id: uuid.UUID | None = None
    sequence: int = Field(ge=0)
    occurred_at: datetime
    payload: dict[str, Any] = Field(default_factory=dict)


# =========================================================
# EVENT PAGE / RESUME
# =========================================================


class WorkspaceChannelRealtimeResumeRequest(
    WorkspaceChannelRealtimeSchema
):
    channel_id: uuid.UUID
    after_sequence: int = Field(default=0, ge=0)
    limit: int = Field(default=100, ge=1, le=200)


class WorkspaceChannelRealtimeEventPage(
    WorkspaceChannelRealtimeSchema
):
    channel_id: uuid.UUID
    events: list[WorkspaceChannelRealtimeEvent] = Field(
        default_factory=list
    )
    next_sequence: int = Field(ge=0)
    has_more: bool = False


# =========================================================
# ACTION RESPONSE
# =========================================================


class WorkspaceChannelRealtimeActionResponse(
    WorkspaceChannelRealtimeSchema
):
    success: bool = True


# =========================================================
# CAPABILITIES
# =========================================================


class WorkspaceChannelRealtimeCapabilities(
    WorkspaceChannelRealtimeSchema
):
    websocket: bool = True
    reconnect_resume: bool = True
    message_events: bool = True
    attachment_events: bool = True
    typing_state: bool = True
    presence_state: bool = True
    heartbeat: bool = True
    workspace_channel_events: bool = True
    redis_fanout: bool = True


__all__ = [
    "WorkspaceChannelAttachmentEventPayload",
    "WorkspaceChannelHeartbeatResponse",
    "WorkspaceChannelLifecycleEventPayload",
    "WorkspaceChannelMessageEventPayload",
    "WorkspaceChannelPresenceEventPayload",
    "WorkspaceChannelPresenceListResponse",
    "WorkspaceChannelPresencePublic",
    "WorkspaceChannelPresenceState",
    "WorkspaceChannelPresenceUpdateRequest",
    "WorkspaceChannelRealtimeActionResponse",
    "WorkspaceChannelRealtimeCapabilities",
    "WorkspaceChannelRealtimeEvent",
    "WorkspaceChannelRealtimeEventPage",
    "WorkspaceChannelRealtimeEventType",
    "WorkspaceChannelRealtimeResumeRequest",
    "WorkspaceChannelRealtimeTicketResponse",
    "WorkspaceChannelSubscribeRequest",
    "WorkspaceChannelTypingEventPayload",
    "WorkspaceChannelTypingRequest",
    "WorkspaceChannelTypingUser",
    "WorkspaceChannelTypingUsersResponse",
    "WorkspaceChannelUnsubscribeRequest",
]