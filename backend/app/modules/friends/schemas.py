from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
)

from .enums import FriendshipStatus


class FriendshipPublic(
    BaseModel
):
    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )

    id: uuid.UUID

    user_low_id: uuid.UUID
    user_high_id: uuid.UUID

    requested_by_user_id: uuid.UUID

    status: FriendshipStatus

    created_at: datetime
    updated_at: datetime

    accepted_at: datetime | None
    blocked_at: datetime | None


class FriendshipListResponse(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
    )

    items: list[
        FriendshipPublic
    ]


class FriendshipActionResponse(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
    )

    success: bool

class FriendUserPublic(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: uuid.UUID
    username: str
    first_name: str | None
    last_name: str | None
    avatar_url: str | None

    @property
    def name(self) -> str:
        full_name = " ".join(
            part
            for part in [self.first_name, self.last_name]
            if part
        ).strip()

        return full_name or self.username