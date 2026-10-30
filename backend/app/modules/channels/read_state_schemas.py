from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class WorkspaceChannelReadStatePublic(
    BaseModel
):
    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )

    channel_id: uuid.UUID
    user_id: uuid.UUID

    last_read_message_id:uuid.UUID | None

    last_read_at:datetime | None

    unread_count: int = Field(
        ge=0,
    )


class WorkspaceChannelUnreadSummary(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
    )

    channel_id: uuid.UUID

    unread_count: int = Field(
        ge=0,
    )

    last_read_message_id:uuid.UUID | None

    last_read_at:datetime | None


class WorkspaceChannelUnreadListResponse(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
    )

    workspace_id:uuid.UUID

    total_unread: int = Field(
        ge=0,
    )

    channels: list[
        WorkspaceChannelUnreadSummary
    ]


__all__ = [
    "WorkspaceChannelReadStatePublic",
    "WorkspaceChannelUnreadListResponse",
    "WorkspaceChannelUnreadSummary",
]