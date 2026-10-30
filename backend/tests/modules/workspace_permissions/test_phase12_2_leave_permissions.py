from __future__ import annotations

from app.modules.workspace_permissions.permissions import (
    WorkspacePermission,
)
from app.modules.workspace_permissions.roles import (
    ADMIN_PERMISSIONS,
    CLIENT_PERMISSIONS,
    MANAGER_PERMISSIONS,
    MEMBER_PERMISSIONS,
    OWNER_PERMISSIONS,
)


def test_owner_has_leave_management():
    assert (
        WorkspacePermission
        .LEAVE_MANAGE
        .value
        in OWNER_PERMISSIONS
    )

    assert (
        WorkspacePermission
        .LEAVE_BALANCE_MANAGE
        .value
        in OWNER_PERMISSIONS
    )


def test_admin_has_full_leave_access():
    expected = {
        WorkspacePermission
        .LEAVE_VIEW
        .value,

        WorkspacePermission
        .LEAVE_MANAGE
        .value,

        WorkspacePermission
        .LEAVE_SELF_READ
        .value,

        WorkspacePermission
        .LEAVE_TEAM_READ
        .value,

        WorkspacePermission
        .LEAVE_ALL_READ
        .value,

        WorkspacePermission
        .LEAVE_APPROVE
        .value,

        WorkspacePermission
        .LEAVE_POLICY_MANAGE
        .value,

        WorkspacePermission
        .LEAVE_BALANCE_MANAGE
        .value,
    }

    assert expected.issubset(
        ADMIN_PERMISSIONS
    )


def test_manager_has_team_leave_access():
    assert (
        WorkspacePermission
        .LEAVE_SELF_READ
        .value
        in MANAGER_PERMISSIONS
    )

    assert (
        WorkspacePermission
        .LEAVE_TEAM_READ
        .value
        in MANAGER_PERMISSIONS
    )

    assert (
        WorkspacePermission
        .LEAVE_APPROVE
        .value
        in MANAGER_PERMISSIONS
    )


def test_manager_cannot_manage_leave_policy():
    assert (
        WorkspacePermission
        .LEAVE_POLICY_MANAGE
        .value
        not in MANAGER_PERMISSIONS
    )

    assert (
        WorkspacePermission
        .LEAVE_BALANCE_MANAGE
        .value
        not in MANAGER_PERMISSIONS
    )


def test_member_has_self_leave_only():
    assert (
        WorkspacePermission
        .LEAVE_SELF_READ
        .value
        in MEMBER_PERMISSIONS
    )

    assert (
        WorkspacePermission
        .LEAVE_TEAM_READ
        .value
        not in MEMBER_PERMISSIONS
    )

    assert (
        WorkspacePermission
        .LEAVE_APPROVE
        .value
        not in MEMBER_PERMISSIONS
    )


def test_client_has_no_leave_access():
    assert (
        WorkspacePermission
        .LEAVE_SELF_READ
        .value
        not in CLIENT_PERMISSIONS
    )

    assert (
        WorkspacePermission
        .LEAVE_VIEW
        .value
        not in CLIENT_PERMISSIONS
    )