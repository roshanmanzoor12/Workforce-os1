from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from .enums import (
    ConversationMemberRole,
    ConversationType,
    MessageType,
    PresenceStatus,
)


class DirectConversationCreateRequest(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
    )

    target_user_id: uuid.UUID


class GroupConversationCreateRequest(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
    )

    name: str = Field(
        min_length=1,
        max_length=120,
    )

    member_user_ids: list[uuid.UUID] = Field(
        min_length=1,
        max_length=99,
    )

    @field_validator(
        "name"
    )
    @classmethod
    def normalize_name(
        cls,
        value: str,
    ) -> str:
        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "Group name cannot be empty."
            )

        return normalized


class ConversationMemberPublic(
    BaseModel
):
    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )

    user_id: uuid.UUID
    role: ConversationMemberRole
    joined_at: datetime
    left_at: datetime | None


class ConversationPublic(
    BaseModel
):
    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )

    id: uuid.UUID
    conversation_type: ConversationType
    name: str | None
    created_by_user_id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime


class MessageCreateRequest(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
    )

    content: str = Field(
        min_length=1,
        max_length=10000,
    )

    @field_validator(
        "content"
    )
    @classmethod
    def normalize_content(
        cls,
        value: str,
    ) -> str:
        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "Message cannot be empty."
            )

        return normalized


class MessageEditRequest(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
    )

    content: str = Field(
        min_length=1,
        max_length=10000,
    )

    @field_validator(
        "content"
    )
    @classmethod
    def normalize_content(
        cls,
        value: str,
    ) -> str:
        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "Message cannot be empty."
            )

        return normalized


class ChatMessagePublic(
    BaseModel
):
    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )

    id: uuid.UUID
    conversation_id: uuid.UUID
    sender_user_id: uuid.UUID | None
    message_type: MessageType
    content: str
    edited_at: datetime | None
    deleted_at: datetime | None
    created_at: datetime


class MessageReceiptPublic(
    BaseModel
):
    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )

    message_id: uuid.UUID
    user_id: uuid.UUID
    read_at: datetime


class PresenceUpdateRequest(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
    )

    status: PresenceStatus


class PresencePublic(
    BaseModel
):
    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )

    user_id: uuid.UUID
    status: PresenceStatus
    last_seen_at: datetime
    updated_at: datetime