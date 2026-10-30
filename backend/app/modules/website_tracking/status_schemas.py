from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
)


class CurrentWebsiteStatusResponse(
    BaseModel
):
    model_config = ConfigDict(
        from_attributes=True,
    )

    device_id: uuid.UUID

    has_active_website: bool

    interval_id: uuid.UUID | None = None

    employee_id: uuid.UUID | None = None

    browser_name: str | None = None
    browser_process_name: str | None = None

    domain: str | None = None
    normalized_domain: str | None = None

    started_at: datetime | None = None
    last_observed_at: datetime | None = None

    duration_seconds: int = 0

    page_url: str | None = None
    page_title: str | None = None


__all__ = [
    "CurrentWebsiteStatusResponse",
]