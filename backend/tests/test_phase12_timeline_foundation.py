from __future__ import annotations

from app.main import app
from app.modules.timeline.enums import (
    TimelineEntityType,
    TimelineEventType,
    TimelineSourceKey,
)
from app.modules.timeline.service import (
    TimelineService,
)
from app.modules.workspace_permissions.permissions import (
    WorkspacePermission,
)
from app.modules.workspace_permissions.policy import (
    WorkspacePermissionPolicy,
)


def test_foundation_event_types_present() -> None:
    values = {
        item.value
        for item
        in TimelineEventType
    }

    assert {
        "goal.created",
        "note.created",
        "knowledge.created",
        "meeting.scheduled",
    }.issubset(
        values
    )


def test_foundation_sources_present() -> None:
    values = {
        item.value
        for item
        in TimelineSourceKey
    }

    assert {
        "goals",
        "notes",
        "knowledge",
        "meetings",
    }.issubset(
        values
    )


def test_foundation_entities_present() -> None:
    values = {
        item.value
        for item
        in TimelineEntityType
    }

    assert {
        "goal",
        "note",
        "knowledge",
        "meeting",
    }.issubset(
        values
    )


def test_attendance_source_now_present() -> None:
    assert (
        TimelineSourceKey.ATTENDANCE
        in list(
            TimelineSourceKey
        )
    )


def test_member_has_self_timeline() -> None:
    assert (
        WorkspacePermissionPolicy
        .allows(
            role_key="member",
            permission=(
                WorkspacePermission
                .TIMELINE_SELF
                .value
            ),
        )
    )


def test_member_cannot_view_other_timeline() -> None:
    assert not (
        WorkspacePermissionPolicy
        .allows(
            role_key="member",
            permission=(
                WorkspacePermission
                .TIMELINE_VIEW
                .value
            ),
        )
    )


def test_admin_can_view_employee_timeline() -> None:
    assert (
        WorkspacePermissionPolicy
        .allows(
            role_key="admin",
            permission=(
                WorkspacePermission
                .TIMELINE_VIEW
                .value
            ),
        )
    )


def test_capabilities_contract() -> None:
    capabilities = (
        TimelineService
        .capabilities()
    )

    assert (
        TimelineSourceKey.GOALS
        in capabilities.sources
    )

    assert (
        TimelineSourceKey.MEETINGS
        in capabilities.sources
    )

    assert (
        TimelineSourceKey.ATTENDANCE
        in capabilities.sources
    )

    assert (
        TimelineEventType
        .GOAL_CREATED
        in capabilities.event_types
    )


def test_timeline_routes_registered() -> None:
    paths = app.openapi()[
        "paths"
    ]

    required = [
        (
            "/api/v1/workspaces/"
            "{workspace_id}/"
            "timeline/capabilities"
        ),
        (
            "/api/v1/workspaces/"
            "{workspace_id}/"
            "timeline/me"
        ),
        (
            "/api/v1/workspaces/"
            "{workspace_id}/"
            "timeline/employees/"
            "{employee_id}"
        ),
    ]

    for path in required:
        assert path in paths


def test_timeline_has_no_database_name_input() -> None:
    schema = app.openapi()

    paths = schema[
        "paths"
    ]

    timeline_paths = {
        key: value
        for key, value
        in paths.items()
        if "/timeline/" in key
    }

    serialized = str(
        timeline_paths
    ).lower()

    assert (
        "database_name"
        not in serialized
    )