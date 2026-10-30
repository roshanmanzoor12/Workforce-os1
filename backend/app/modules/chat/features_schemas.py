from __future__ import annotations

import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from .schemas import ChatMessagePublic


class FeatureMessageCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    content: str = Field(min_length=1, max_length=10000)
    client_message_id: uuid.UUID
    reply_to_message_id: uuid.UUID | None = None


class FeatureMessagePublic(ChatMessagePublic):
    client_message_id: uuid.UUID | None = None
    reply_to_message_id: uuid.UUID | None = None
    reactions: dict[str, int] = Field(default_factory=dict)
    pinned: bool = False
    delivered_at: datetime | None = None
    read_at: datetime | None = None


class ReactionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    emoji: str = Field(min_length=1, max_length=32)


class ConversationPreferencePatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    pinned: bool | None = None
    muted: bool | None = None
    archived: bool | None = None


class ConversationFeatureSummary(BaseModel):
    conversation_id: uuid.UUID
    unread_count: int
    pinned: bool
    muted: bool
    archived: bool
    last_read_at: datetime | None


class DeliveryPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    message_id: uuid.UUID
    user_id: uuid.UUID
    delivered_at: datetime
    read_at: datetime | None
