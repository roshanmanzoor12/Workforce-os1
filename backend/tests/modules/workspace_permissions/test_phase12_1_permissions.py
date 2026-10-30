from app.modules.workspace_permissions.permissions import (
    ALL_WORKSPACE_PERMISSIONS,
    WorkspacePermission,
)
from app.modules.workspace_permissions.roles import (
    ADMIN_PERMISSIONS,
    CLIENT_PERMISSIONS,
    MANAGER_PERMISSIONS,
    MEMBER_PERMISSIONS,
    OWNER_PERMISSIONS,
)


def test_phase12_1_permissions_registered():
    required = {
        WorkspacePermission
        .SHIFTS_VIEW
        .value,

        WorkspacePermission
        .SHIFTS_MANAGE
        .value,

        WorkspacePermission
        .SHIFTS_SELF_READ
        .value,

        WorkspacePermission
        .SHIFTS_TEAM_READ
        .value,

        WorkspacePermission
        .SHIFTS_ALL_READ
        .value,

        WorkspacePermission
        .HOLIDAYS_VIEW
        .value,

        WorkspacePermission
        .HOLIDAYS_MANAGE
        .value,

        WorkspacePermission
        .HOLIDAYS_SELF_READ
        .value,

        WorkspacePermission
        .HOLIDAYS_TEAM_READ
        .value,

        WorkspacePermission
        .HOLIDAYS_ALL_READ
        .value,
    }

    assert required.issubset(
        ALL_WORKSPACE_PERMISSIONS
    )


def test_owner_has_every_phase12_1_permission():
    assert (
        WorkspacePermission
        .SHIFTS_MANAGE
        .value
        in OWNER_PERMISSIONS
    )

    assert (
        WorkspacePermission
        .HOLIDAYS_MANAGE
        .value
        in OWNER_PERMISSIONS
    )


def test_admin_has_full_scheduling_access():
    expected = {
        WorkspacePermission
        .SHIFTS_VIEW
        .value,

        WorkspacePermission
        .SHIFTS_MANAGE
        .value,

        WorkspacePermission
        .SHIFTS_ALL_READ
        .value,

        WorkspacePermission
        .HOLIDAYS_VIEW
        .value,

        WorkspacePermission
        .HOLIDAYS_MANAGE
        .value,

        WorkspacePermission
        .HOLIDAYS_ALL_READ
        .value,
    }

    assert expected.issubset(
        ADMIN_PERMISSIONS
    )


def test_manager_has_team_schedule_access():
    assert (
        WorkspacePermission
        .SHIFTS_TEAM_READ
        .value
        in MANAGER_PERMISSIONS
    )

    assert (
        WorkspacePermission
        .HOLIDAYS_TEAM_READ
        .value
        in MANAGER_PERMISSIONS
    )


def test_manager_does_not_manage_schedules_by_default():
    assert (
        WorkspacePermission
        .SHIFTS_MANAGE
        .value
        not in MANAGER_PERMISSIONS
    )

    assert (
        WorkspacePermission
        .HOLIDAYS_MANAGE
        .value
        not in MANAGER_PERMISSIONS
    )


def test_member_has_self_schedule_access():
    assert (
        WorkspacePermission
        .SHIFTS_SELF_READ
        .value
        in MEMBER_PERMISSIONS
    )

    assert (
        WorkspacePermission
        .HOLIDAYS_SELF_READ
        .value
        in MEMBER_PERMISSIONS
    )


def test_member_cannot_manage_schedules():
    assert (
        WorkspacePermission
        .SHIFTS_MANAGE
        .value
        not in MEMBER_PERMISSIONS
    )

    assert (
        WorkspacePermission
        .HOLIDAYS_MANAGE
        .value
        not in MEMBER_PERMISSIONS
    )


def test_client_has_no_internal_schedule_permissions():
    forbidden = {
        WorkspacePermission
        .SHIFTS_VIEW
        .value,

        WorkspacePermission
        .SHIFTS_MANAGE
        .value,

        WorkspacePermission
        .SHIFTS_SELF_READ
        .value,

        WorkspacePermission
        .SHIFTS_TEAM_READ
        .value,

        WorkspacePermission
        .SHIFTS_ALL_READ
        .value,

        WorkspacePermission
        .HOLIDAYS_VIEW
        .value,

        WorkspacePermission
        .HOLIDAYS_MANAGE
        .value,

        WorkspacePermission
        .HOLIDAYS_SELF_READ
        .value,

        WorkspacePermission
        .HOLIDAYS_TEAM_READ
        .value,

        WorkspacePermission
        .HOLIDAYS_ALL_READ
        .value,
    }

    assert forbidden.isdisjoint(
        CLIENT_PERMISSIONS
    )