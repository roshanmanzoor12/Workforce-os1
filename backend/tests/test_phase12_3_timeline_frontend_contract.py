from __future__ import annotations

from datetime import (
    datetime,
    timezone,
)

import pytest

from app.main import app
from app.modules.timeline.enums import (
    TimelineEventType,
    TimelineSourceKey,
)
from app.modules.timeline.factory import (
    build_timeline_query,
)
from app.modules.timeline.service import (
    TimelineService,
)


def test_query_factory() -> None:
    query = build_timeline_query(
        before=None,
        after=None,
        limit=50,
        sources=[
            TimelineSourceKey
            .ATTENDANCE,
        ],
        event_types=[
            TimelineEventType
            .ATTENDANCE_CHECK_IN,
        ],
        cursor=None,
    )

    assert (
        query.limit
        == 50
    )

    assert (
        TimelineSourceKey
        .ATTENDANCE
        in query.sources
    )

    assert (
        TimelineEventType
        .ATTENDANCE_CHECK_IN
        in query.event_types
    )


def test_invalid_date_window() -> None:
    current = datetime(
        2026,
        9,
        18,
        10,
        0,
        tzinfo=timezone.utc,
    )

    with pytest.raises(
        ValueError
    ):
        build_timeline_query(
            before=current,
            after=current,
            limit=50,
            sources=None,
            event_types=None,
            cursor=None,
        )


def test_capabilities_are_frontend_ready() -> None:
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
        capabilities
        .supports_source_filtering
        is True
    )

    assert (
        capabilities
        .supports_event_filtering
        is True
    )

    assert (
        capabilities
        .supports_date_filtering
        is True
    )

    assert (
        capabilities
        .max_page_size
        == 200
    )


def test_self_timeline_response_contract() -> None:
    schema = app.openapi()

    path = (
        "/api/v1/workspaces/"
        "{workspace_id}/timeline/me"
    )

    operation = schema[
        "paths"
    ][
        path
    ][
        "get"
    ]

    assert (
        "200"
        in operation[
            "responses"
        ]
    )


def test_employee_timeline_registered() -> None:
    paths = app.openapi()[
        "paths"
    ]

    assert (
        "/api/v1/workspaces/"
        "{workspace_id}/timeline/"
        "employees/{employee_id}"
        in paths
    )


def test_capabilities_route_registered() -> None:
    paths = app.openapi()[
        "paths"
    ]

    assert (
        "/api/v1/workspaces/"
        "{workspace_id}/timeline/"
        "capabilities"
        in paths
    )