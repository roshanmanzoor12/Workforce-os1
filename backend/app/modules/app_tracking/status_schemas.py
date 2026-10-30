from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    Field,
)


class CurrentAppStatusResponse(BaseModel):
    device_uuid: UUID

    has_observation: bool

    process_name: str | None = None

    executable_path: str | None = None

    window_title: str | None = None

    app_key: str | None = None

    observed_at: datetime | None = None

    interval_id: UUID | None = None

    interval_started_at: datetime | None = None

    duration_seconds: int | None = Field(
        default=None,
        ge=0,
    )


__all__ = [
    "CurrentAppStatusResponse",
]