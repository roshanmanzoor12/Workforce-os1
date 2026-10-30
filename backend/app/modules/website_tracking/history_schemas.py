from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class WebsiteUsageHistoryItem(
    BaseModel
):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: uuid.UUID
    device_id: uuid.UUID
    employee_id: uuid.UUID | None

    browser_name: str
    browser_process_name: str

    domain: str
    normalized_domain: str

    status: str

    started_at: datetime
    ended_at: datetime | None
    last_observed_at: datetime

    duration_seconds: int = Field(
        ge=0
    )


class WebsiteUsageHistoryResponse(
    BaseModel
):
    items: list[
        WebsiteUsageHistoryItem
    ]

    count: int = Field(
        ge=0
    )


class WebsiteUsageAggregateItem(
    BaseModel
):
    normalized_domain: str

    domain: str

    duration_seconds: int = Field(
        ge=0
    )

    interval_count: int = Field(
        ge=0
    )


class WebsiteUsageAggregateResponse(
    BaseModel
):
    items: list[
        WebsiteUsageAggregateItem
    ]

    total_seconds: int = Field(
        ge=0
    )

    interval_count: int = Field(
        ge=0
    )


__all__ = [
    "WebsiteUsageHistoryItem",
    "WebsiteUsageHistoryResponse",
    "WebsiteUsageAggregateItem",
    "WebsiteUsageAggregateResponse",
]