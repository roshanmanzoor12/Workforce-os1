from __future__ import annotations

from app.main import app
from app.modules.timeline.enums import (
    TimelineEventType,
    TimelineSourceKey,
)
from app.modules.timeline.filters import (
    TimelineFilter,
)
from app.modules.timeline.service import (
    TimelineService,
)


def test_source_filter() -> None:
    query_filter = TimelineFilter(
        sources=frozenset(
            {
                TimelineSourceKey.GOALS,
            }
        )
    )

    assert query_filter.allows_source(
        TimelineSourceKey.GOALS
    )

    assert not query_filter.allows_source(
        TimelineSourceKey.NOTES
    )


def test_event_type_filter() -> None:
    query_filter = TimelineFilter(
        event_types=frozenset(
            {
                TimelineEventType
                .NOTE_CREATED,
            }
        )
    )

    assert (
        query_filter
        .allows_event_type(
            TimelineEventType
            .NOTE_CREATED
        )
    )

    assert not (
        query_filter
        .allows_event_type(
            TimelineEventType
            .GOAL_CREATED
        )
    )


def test_empty_filters_allow_all() -> None:
    query_filter = (
        TimelineFilter()
    )

    assert query_filter.allows_source(
        TimelineSourceKey.GOALS
    )

    assert (
        query_filter
        .allows_event_type(
            TimelineEventType
            .MEETING_SCHEDULED
        )
    )


def test_capabilities_support_cursor() -> None:
    capabilities = (
        TimelineService
        .capabilities()
    )

    assert (
        capabilities
        .supports_cursor_pagination
        is True
    )

    assert (
        capabilities.max_page_size
        == 200
    )


def test_timeline_query_parameters() -> None:
    schema = app.openapi()

    operation = schema[
        "paths"
    ][
        (
            "/api/v1/workspaces/"
            "{workspace_id}/timeline/me"
        )
    ][
        "get"
    ]

    parameters = {
        item["name"]
        for item
        in operation[
            "parameters"
        ]
    }

    assert {
        "before",
        "after",
        "limit",
        "source",
        "event_type",
        "cursor",
    }.issubset(
        parameters
    )


def test_employee_timeline_query_parameters() -> None:
    schema = app.openapi()

    operation = schema[
        "paths"
    ][
        (
            "/api/v1/workspaces/"
            "{workspace_id}/timeline/"
            "employees/{employee_id}"
        )
    ][
        "get"
    ]

    parameters = {
        item["name"]
        for item
        in operation[
            "parameters"
        ]
    }

    assert "cursor" in parameters
    assert "source" in parameters
    assert "event_type" in parameters