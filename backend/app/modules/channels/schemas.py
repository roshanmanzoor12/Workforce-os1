from __future__ import annotations

import re
import uuid
from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from .enums import (
    WorkspaceChannelMessageType,
    WorkspaceChannelRole,
    WorkspaceChannelType,
)


def make_channel_slug(
    value: str,
) -> str:
    normalized = value.strip().lower()

    normalized = re.sub(
        r"[^a-z0-9]+",
        "-",
        normalized,
    )

    normalized = normalized.strip(
        "-"
    )

    if not normalized:
        raise ValueError(
            "Channel name must contain "
            "letters or numbers."
        )

    return normalized[:120]


class WorkspaceChannelCreateRequest(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
    )

    workspace_id: uuid.UUID

    name: str = Field(
        min_length=1,
        max_length=120,
    )

    channel_type: WorkspaceChannelType = (
        WorkspaceChannelType.TEXT
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
                "Channel name cannot be empty."
            )

        make_channel_slug(
            normalized
        )

        return normalized


class WorkspaceChannelUpdateRequest(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
    )

    name: str = Field(
        min_length=1,
        max_length=120,
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
                "Channel name cannot be empty."
            )

        make_channel_slug(
            normalized
        )

        return normalized


class WorkspaceChannelPublic(
    BaseModel
):
    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )

    id: uuid.UUID
    workspace_id: uuid.UUID

    name: str
    slug: str

    channel_type: WorkspaceChannelType

    created_by_user_id: uuid.UUID

    is_active: bool

    created_at: datetime
    updated_at: datetime


class WorkspaceChannelMemberPublic(
    BaseModel
):
    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )

    channel_id: uuid.UUID
    user_id: uuid.UUID

    role: WorkspaceChannelRole

    joined_at: datetime
    left_at: datetime | None


class WorkspaceChannelMessageCreateRequest(
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


class WorkspaceChannelMessageUpdateRequest(
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


class WorkspaceChannelMessagePublic(
    BaseModel
):
    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )

    id: uuid.UUID
    channel_id: uuid.UUID

    sender_user_id: uuid.UUID | None

    message_type: (
        WorkspaceChannelMessageType
    )

    content: str

    edited_at: datetime | None
    deleted_at: datetime | None

    created_at: datetime


__all__ = [
    "WorkspaceChannelCreateRequest",
    "WorkspaceChannelMemberPublic",
    "WorkspaceChannelMessageCreateRequest",
    "WorkspaceChannelMessagePublic",
    "WorkspaceChannelMessageUpdateRequest",
    "WorkspaceChannelPublic",
    "WorkspaceChannelUpdateRequest",
    "make_channel_slug",
]