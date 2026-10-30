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
class TimelineQuery:
    before: datetime | None = None
    after: datetime | None = None

    limit: int = 50

    sources: frozenset[
        TimelineSourceKey
    ] = frozenset()

    event_types: frozenset[
        TimelineEventType
    ] = frozenset()

    cursor: str | None = None

    def validate(
        self,
    ) -> None:
        if self.limit < 1:
            raise ValueError(
                "Timeline limit must be at least 1."
            )

        if self.limit > 200:
            raise ValueError(
                "Timeline limit cannot exceed 200."
            )

        if (
            self.before is not None
            and self.after is not None
            and self.after >= self.before
        ):
            raise ValueError(
                "after must be earlier than before."
            )


__all__ = [
    "TimelineQuery",
]