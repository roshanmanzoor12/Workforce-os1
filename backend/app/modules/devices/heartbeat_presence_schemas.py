from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


__all__ = [
    "DevicePresenceResponse",
]


class DevicePresenceResponse(BaseModel):
    """
    Server-derived device presence.

    `is_online` is never trusted from the endpoint agent.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    device_uuid: UUID

    is_online: bool

    last_seen_at: datetime | None

    offline_since: datetime | None

    online_timeout_seconds: int