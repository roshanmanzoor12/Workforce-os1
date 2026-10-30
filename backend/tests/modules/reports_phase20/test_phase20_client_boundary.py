from __future__ import annotations

from app.modules.workspace_permissions.permissions import (
    WorkspacePermission,
)
from app.modules.workspace_permissions.roles import (
    CLIENT_PERMISSIONS,
)


def test_client_has_no_workspace_report_scope_by_default():
    assert (
        WorkspacePermission
        .REPORTS_ALL_READ
        .value
        not in CLIENT_PERMISSIONS
    )


def test_client_has_no_team_report_scope_by_default():
    assert (
        WorkspacePermission
        .REPORTS_TEAM_READ
        .value
        not in CLIENT_PERMISSIONS
    )


def test_client_has_no_report_export_by_default():
    assert (
        WorkspacePermission
        .REPORTS_EXPORT
        .value
        not in CLIENT_PERMISSIONS
    )


def test_client_can_have_self_shared_report_surface():
    assert (
        WorkspacePermission
        .REPORTS_SELF_READ
        .value
        in CLIENT_PERMISSIONS
    )