from __future__ import annotations

from datetime import datetime

from app.modules.timeline.enums import (
    TimelineEventType,
    TimelineSourceKey,
)
from app.modules.timeline.query import (
    TimelineQuery,
)


def build_timeline_query(
    *,
    before: datetime | None,
    after: datetime | None,
    limit: int,
    sources: list[
        TimelineSourceKey
    ]
    | None,
    event_types: list[
        TimelineEventType
    ]
    | None,
    cursor: str | None,
) -> TimelineQuery:
    query = TimelineQuery(
        before=before,
        after=after,
        limit=limit,
        sources=frozenset(
            sources
            or []
        ),
        event_types=frozenset(
            event_types
            or []
        ),
        cursor=cursor,
    )

    query.validate()

    return query


__all__ = [
    "build_timeline_query",
]