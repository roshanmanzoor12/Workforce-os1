from __future__ import annotations

import json
import uuid
from datetime import (
    datetime,
    timezone,
)
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from .realtime_enums import (
    ChatRealtimeEventType,
)


class ChatRealtimeEvent(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
    )

    event_id: uuid.UUID = Field(
        default_factory=uuid.uuid4
    )

    event_type: ChatRealtimeEventType

    occurred_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )

    conversation_id: uuid.UUID | None = None

    actor_user_id: uuid.UUID | None = None

    target_user_id: uuid.UUID | None = None

    data: dict[
        str,
        Any,
    ] = Field(
        default_factory=dict
    )

    def to_json(
        self,
    ) -> str:
        return self.model_dump_json()

    @classmethod
    def from_json(
        cls,
        value: str | bytes,
    ) -> "ChatRealtimeEvent":
        if isinstance(
            value,
            bytes,
        ):
            value = value.decode(
                "utf-8"
            )

        return cls.model_validate_json(
            value
        )


def serialize_event(
    event: ChatRealtimeEvent,
) -> str:
    return event.to_json()


def deserialize_event(
    value: str | bytes,
) -> ChatRealtimeEvent:
    return ChatRealtimeEvent.from_json(
        value
    )


__all__ = [
    "ChatRealtimeEvent",
    "deserialize_event",
    "serialize_event",
]