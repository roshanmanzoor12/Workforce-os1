from __future__ import annotations

import uuid
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from .realtime_client_protocol import (
    RealtimeClientCommandType,
    RealtimeServerEventType,
)


class RealtimeClientCommand(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
    )

    command: RealtimeClientCommandType

    conversation_id: (
        uuid.UUID
        | None
    ) = None

    cursor: str | None = Field(
        default=None,
        max_length=1000,
    )


class RealtimeServerEnvelope(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
    )

    event: RealtimeServerEventType

    data: dict[
        str,
        Any,
    ] = Field(
        default_factory=dict
    )


class RealtimeResumeRequest(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
    )

    conversation_id: uuid.UUID

    cursor: str | None = Field(
        default=None,
        max_length=1000,
    )

    limit: int = Field(
        default=50,
        ge=1,
        le=100,
    )


__all__ = [
    "RealtimeClientCommand",
    "RealtimeResumeRequest",
    "RealtimeServerEnvelope",
]