from __future__ import annotations

from app.main import app
from app.modules.meetings.migration_contract import (
    MEETINGS_TENANT_DOWN_REVISION,
    MEETINGS_TENANT_REVISION,
)
from app.modules.workspace_permissions.policy import (
    WorkspacePermissionPolicy,
)
from app.modules.workspace_permissions.permissions import (
    WorkspacePermission,
)


def test_tenant_revision_contract(
) -> None:
    assert (
        MEETINGS_TENANT_REVISION
        == "d3e4f5a6b7c8"
    )

    assert (
        MEETINGS_TENANT_DOWN_REVISION
        == "c2d3e4f5a6b7"
    )


def test_owner_has_full_monitoring_access(
) -> None:
    required = [
        WorkspacePermission
        .MONITORING_VIEW
        .value,
        WorkspacePermission
        .MONITORING_MANAGE
        .value,
        WorkspacePermission
        .MONITORING_LIVE_VIEW
        .value,
        WorkspacePermission
        .MONITORING_SETTINGS_MANAGE
        .value,
    ]

    for permission in required:
        assert (
            WorkspacePermissionPolicy
            .allows(
                role_key="owner",
                permission=permission,
            )
        )


def test_member_has_meeting_access(
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

    assert (
        WorkspacePermissionPolicy
        .allows(
            role_key="member",
            permission=(
                WorkspacePermission
                .MEETINGS_CREATE
                .value
            ),
        )
    )


def test_member_cannot_manage_monitoring(
) -> None:
    assert not (
        WorkspacePermissionPolicy
        .allows(
            role_key="member",
            permission=(
                WorkspacePermission
                .MONITORING_MANAGE
                .value
            ),
        )
    )


def test_phase11_8_core_routes(
) -> None:
    paths = app.openapi()[
        "paths"
    ]

    required = [
        (
            "/api/v1/workspaces/"
            "{workspace_id}/permissions/me"
        ),
        (
            "/api/v1/workspaces/"
            "{workspace_id}/meetings"
        ),
        (
            "/api/v1/workspaces/"
            "{workspace_id}/meetings/"
            "{meeting_id}/start"
        ),
        (
            "/api/v1/workspaces/"
            "{workspace_id}/meetings/"
            "{meeting_id}/end"
        ),
        (
            "/api/v1/workspaces/"
            "{workspace_id}/meetings/"
            "me/invitations"
        ),
        (
            "/api/v1/workspaces/"
            "{workspace_id}/"
            "monitoring-control"
        ),
    ]

    for path in required:
        assert path in paths