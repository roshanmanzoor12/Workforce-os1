from __future__ import annotations

from app.main import app
from app.modules.meetings.enums import (
    MeetingParticipantStatus,
)
from app.modules.workspace_permissions.permissions import (
    WorkspacePermission,
)
from app.modules.workspace_permissions.policy import (
    WorkspacePermissionPolicy,
)


def test_participant_response_values(
) -> None:
    assert (
        MeetingParticipantStatus
        .ACCEPTED
        .value
        == "accepted"
    )

    assert (
        MeetingParticipantStatus
        .DECLINED
        .value
        == "declined"
    )


def test_member_can_view_meetings(
) -> None:
    assert (
        WorkspacePermissionPolicy
        .allows(
            role_key="member",
            permission=(
                WorkspacePermission
                .MEETINGS_VIEW
                .value
            ),
        )
    )


def test_member_cannot_view_monitoring(
) -> None:
    assert not (
        WorkspacePermissionPolicy
        .allows(
            role_key="member",
            permission=(
                WorkspacePermission
                .MONITORING_VIEW
                .value
            ),
        )
    )


def test_admin_can_view_monitoring(
) -> None:
    assert (
        WorkspacePermissionPolicy
        .allows(
            role_key="admin",
            permission=(
                WorkspacePermission
                .MONITORING_VIEW
                .value
            ),
        )
    )


def test_admin_can_view_live_screen(
) -> None:
    assert (
        WorkspacePermissionPolicy
        .allows(
            role_key="admin",
            permission=(
                WorkspacePermission
                .MONITORING_LIVE_VIEW
                .value
            ),
        )
    )


def test_meeting_self_routes_exist(
) -> None:
    paths = app.openapi().get(
        "paths",
        {},
    )

    expected = {
        (
            "/api/v1/workspaces/"
            "{workspace_id}/meetings/"
            "me/invitations"
        ): {
            "get",
        },
        (
            "/api/v1/workspaces/"
            "{workspace_id}/meetings/"
            "me/{meeting_id}/response"
        ): {
            "patch",
        },
    }

    for path, methods in expected.items():
        assert path in paths

        actual = {
            method.lower()
            for method
            in paths[path].keys()
        }

        assert methods.issubset(
            actual
        )


def test_monitoring_control_routes_exist(
) -> None:
    paths = app.openapi().get(
        "paths",
        {},
    )

    expected = {
        (
            "/api/v1/workspaces/"
            "{workspace_id}/"
            "monitoring-control"
        ): {
            "get",
        },
        (
            "/api/v1/workspaces/"
            "{workspace_id}/"
            "monitoring-control/live-access"
        ): {
            "get",
        },
        (
            "/api/v1/workspaces/"
            "{workspace_id}/"
            "monitoring-control/"
            "manage-access"
        ): {
            "get",
        },
        (
            "/api/v1/workspaces/"
            "{workspace_id}/"
            "monitoring-control/"
            "settings-access"
        ): {
            "get",
        },
    }

    for path, methods in expected.items():
        assert path in paths

        actual = {
            method.lower()
            for method
            in paths[path].keys()
        }

        assert methods.issubset(
            actual
        )