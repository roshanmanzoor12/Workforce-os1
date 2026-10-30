from __future__ import annotations

from app.modules.workspace_permissions.permissions import (
    WorkspacePermission,
)


def test_report_permissions_exist():
    assert (
        WorkspacePermission
        .REPORTS_SELF_READ
        .value
        == "reports.self.read"
    )

    assert (
        WorkspacePermission
        .REPORTS_TEAM_READ
        .value
        == "reports.team.read"
    )

    assert (
        WorkspacePermission
        .REPORTS_ALL_READ
        .value
        == "reports.all.read"
    )

    assert (
        WorkspacePermission
        .REPORTS_EXPORT
        .value
        == "reports.export"
    )


def test_export_is_separate_permission():
    read_permissions = {
        WorkspacePermission
        .REPORTS_SELF_READ
        .value,

        WorkspacePermission
        .REPORTS_TEAM_READ
        .value,

        WorkspacePermission
        .REPORTS_ALL_READ
        .value,
    }

    assert (
        WorkspacePermission
        .REPORTS_EXPORT
        .value
        not in read_permissions
    )