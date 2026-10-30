from __future__ import annotations

from unittest.mock import MagicMock

from app.modules.timeline.enums import (
    TimelineSourceKey,
)
from app.modules.timeline.registry import (
    TimelineSourceRegistry,
)
from app.modules.timeline.sources import (
    AttendanceTimelineSource,
    GoalTimelineSource,
    KnowledgeTimelineSource,
    MeetingTimelineSource,
    NoteTimelineSource,
)


def build_registry(
) -> TimelineSourceRegistry:
    session = MagicMock()

    return TimelineSourceRegistry(
        session
    )


def test_registry_contains_all_sources() -> None:
    registry = build_registry()

    keys = set(
        registry.keys()
    )

    assert keys == {
        TimelineSourceKey.GOALS,
        TimelineSourceKey.NOTES,
        TimelineSourceKey.KNOWLEDGE,
        TimelineSourceKey.MEETINGS,
        TimelineSourceKey.ATTENDANCE,
    }


def test_registry_source_types() -> None:
    registry = build_registry()

    sources = {
        item.key: item.source
        for item
        in registry.all()
    }

    assert isinstance(
        sources[
            TimelineSourceKey.GOALS
        ],
        GoalTimelineSource,
    )

    assert isinstance(
        sources[
            TimelineSourceKey.NOTES
        ],
        NoteTimelineSource,
    )

    assert isinstance(
        sources[
            TimelineSourceKey
            .KNOWLEDGE
        ],
        KnowledgeTimelineSource,
    )

    assert isinstance(
        sources[
            TimelineSourceKey
            .MEETINGS
        ],
        MeetingTimelineSource,
    )

    assert isinstance(
        sources[
            TimelineSourceKey
            .ATTENDANCE
        ],
        AttendanceTimelineSource,
    )


def test_registry_can_select_attendance_only() -> None:
    registry = build_registry()

    selected = (
        registry.selected(
            frozenset(
                {
                    TimelineSourceKey
                    .ATTENDANCE
                }
            )
        )
    )

    assert len(
        selected
    ) == 1

    assert (
        selected[0].key
        == (
            TimelineSourceKey
            .ATTENDANCE
        )
    )

    assert isinstance(
        selected[0].source,
        AttendanceTimelineSource,
    )


def test_empty_selection_returns_every_source() -> None:
    registry = build_registry()

    assert (
        len(
            registry.selected(
                frozenset()
            )
        )
        == 5
    )