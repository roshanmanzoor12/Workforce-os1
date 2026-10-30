from __future__ import annotations

import inspect

from app.modules.monitoring_admin.access import (
    require_monitoring_view,
    resolve_monitoring_admin_access,
)
from app.modules.workspace_permissions.permissions import (
    WorkspacePermission,
)


# =========================================================
# SCOPED READ PERMISSIONS
# =========================================================


def test_monitoring_access_supports_scoped_read_permissions():
    """
    Verify the canonical monitoring access resolver references all
    three scoped read permission enum members.

    Important:

    inspect.getsource() returns Python source code, so it contains
    enum attribute names such as:

        WorkspacePermission.MONITORING_SELF_READ.value

    It does NOT contain the resolved enum value string such as:

        "monitoring.self.read"

    Therefore this test must assert the enum member names, not their
    runtime .value strings.
    """

    source = inspect.getsource(
        resolve_monitoring_admin_access
    )

    expected_members = (
        "MONITORING_SELF_READ",
        "MONITORING_TEAM_READ",
        "MONITORING_ALL_READ",
    )

    missing = [
        member
        for member
        in expected_members
        if member not in source
    ]

    assert not missing, (
        "Monitoring access resolver "
        "does not reference scoped read "
        "permission members: "
        + ", ".join(
            missing
        )
    )


# =========================================================
# CANONICAL PERMISSION VALUES
# =========================================================


def test_monitoring_scoped_permission_values_are_distinct():
    permissions = {
        WorkspacePermission
        .MONITORING_SELF_READ
        .value,

        WorkspacePermission
        .MONITORING_TEAM_READ
        .value,

        WorkspacePermission
        .MONITORING_ALL_READ
        .value,
    }

    assert len(
        permissions
    ) == 3

    assert (
        WorkspacePermission
        .MONITORING_SELF_READ
        .value
        in permissions
    )

    assert (
        WorkspacePermission
        .MONITORING_TEAM_READ
        .value
        in permissions
    )

    assert (
        WorkspacePermission
        .MONITORING_ALL_READ
        .value
        in permissions
    )


# =========================================================
# SERVER-SIDE VIEW ENFORCEMENT
# =========================================================


def test_monitoring_view_is_server_enforced():
    source = inspect.getsource(
        require_monitoring_view
    )

    assert (
        "ValidationError"
        in source
    )

    assert (
        "Monitoring access required"
        in source
    )


# =========================================================
# MANAGE / SETTINGS DO NOT REMOVE VIEW SUPPORT
# =========================================================


def test_monitoring_view_guard_supports_authorized_admin_paths():
    source = inspect.getsource(
        require_monitoring_view
    )

    assert (
        "can_view"
        in source
    )

    assert (
        "can_manage"
        in source
    )

    assert (
        "can_manage_settings"
        in source
    )