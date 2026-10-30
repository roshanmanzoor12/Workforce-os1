from __future__ import annotations

from pydantic import (
    BaseModel,
    ConfigDict,
)

from .schemas import (
    ChatMessagePublic,
)


class ChatMessagePagePublic(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
    )

    items: list[
        ChatMessagePublic
    ]

    next_cursor: str | None

    has_more: bool


__all__ = [
    "ChatMessagePagePublic",
]