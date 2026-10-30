from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    Field,
)


class AppUsageHistoryItem(BaseModel):
    id: UUID

    device_id: UUID
    employee_id: UUID | None

    app_key: str
    process_name: str

    executable_path: str | None

    status: str

    started_at: datetime
    ended_at: datetime | None
    last_observed_at: datetime

    duration_seconds: int = Field(
        ge=0
    )


class AppUsageHistoryResponse(BaseModel):
    items: list[
        AppUsageHistoryItem
    ]

    count: int = Field(
        ge=0
    )


class AppUsageAggregateItem(BaseModel):
    app_key: str
    process_name: str

    duration_seconds: int = Field(
        ge=0
    )

    interval_count: int = Field(
        ge=0
    )


class AppUsageAggregateResponse(BaseModel):
    items: list[
        AppUsageAggregateItem
    ]

    total_seconds: int = Field(
        ge=0
    )

    interval_count: int = Field(
        ge=0
    )


__all__ = [
    "AppUsageHistoryItem",
    "AppUsageHistoryResponse",
    "AppUsageAggregateItem",
    "AppUsageAggregateResponse",
]