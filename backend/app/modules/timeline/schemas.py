from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from app.modules.timeline.enums import (
    TimelineEntityType,
    TimelineEventType,
    TimelineSourceKey,
)


class TimelineSchema(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid",
    )


class TimelineEvent(
    TimelineSchema
):
    event_id: str = Field(
        min_length=1,
        max_length=200,
    )

    event_type: TimelineEventType

    source: TimelineSourceKey

    entity_type: TimelineEntityType

    entity_id: uuid.UUID

    employee_id: uuid.UUID

    occurred_at: datetime

    title: str = Field(
        min_length=1,
        max_length=500,
    )

    summary: str | None = Field(
        default=None,
        max_length=5000,
    )

    metadata: dict[
        str,
        Any,
    ] = Field(
        default_factory=dict,
    )


class TimelineResponse(
    TimelineSchema
):
    employee_id: uuid.UUID

    items: list[
        TimelineEvent
    ]

    total: int = Field(
        ge=0,
    )

    limit: int = Field(
        ge=1,
        le=200,
    )

    before: datetime | None = None

    after: datetime | None = None

    next_cursor: str | None = None

    has_more: bool = False

    applied_sources: list[
        TimelineSourceKey
    ] = Field(
        default_factory=list,
    )

    applied_event_types: list[
        TimelineEventType
    ] = Field(
        default_factory=list,
    )


class TimelineCapabilities(
    TimelineSchema
):
    sources: list[
        TimelineSourceKey
    ]

    event_types: list[
        TimelineEventType
    ]

    supports_cursor_pagination: bool = True

    supports_source_filtering: bool = True

    supports_event_filtering: bool = True

    supports_date_filtering: bool = True

    max_page_size: int = Field(
        default=200,
        ge=1,
        le=200,
    )


__all__ = [
    "TimelineEvent",
    "TimelineResponse",
    "TimelineCapabilities",
]