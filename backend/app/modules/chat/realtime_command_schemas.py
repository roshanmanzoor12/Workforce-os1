from __future__ import annotations

import uuid

from pydantic import (
    BaseModel,
    ConfigDict,
)


class RealtimeActionResponse(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
    )

    success: bool


class TypingUsersResponse(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
    )

    user_ids: list[
        uuid.UUID
    ]


class HeartbeatResponse(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
    )

    online: bool

    heartbeat_unix: int

    expires_in_seconds: int


__all__ = [
    "HeartbeatResponse",
    "RealtimeActionResponse",
    "TypingUsersResponse",
]