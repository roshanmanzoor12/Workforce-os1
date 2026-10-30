from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.modules.timeline.enums import (
    TimelineEventType,
    TimelineSourceKey,
)


@dataclass(
    frozen=True,
    slots=True,
)
class TimelineFilter:
    before: datetime | None = None
    after: datetime | None = None

    sources: frozenset[
        TimelineSourceKey
    ] = frozenset()

    event_types: frozenset[
        TimelineEventType
    ] = frozenset()

    def validate(
        self,
    ) -> None:
        if (
            self.before is not None
            and self.after is not None
            and self.after >= self.before
        ):
            raise ValueError(
                "after must be earlier than before."
            )

    def allows_source(
        self,
        source: TimelineSourceKey,
    ) -> bool:
        if not self.sources:
            return True

        return source in self.sources

    def allows_event_type(
        self,
        event_type: TimelineEventType,
    ) -> bool:
        if not self.event_types:
            return True

        return event_type in self.event_types


__all__ = [
    "TimelineFilter",
]