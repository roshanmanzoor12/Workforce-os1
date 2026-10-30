from __future__ import annotations

from app.modules.workspace_permissions.permissions import (
    WorkspacePermission,
)
from app.modules.workspace_permissions.policy import (
    WorkspacePermissionPolicy,
)
from app.modules.workspace_permissions.roles import (
    WORKSPACE_ROLE_ADMIN,
    WORKSPACE_ROLE_MEMBER,
    WORKSPACE_ROLE_OWNER,
)


def test_owner_has_all_permissions(
) -> None:
    permissions = (
        WorkspacePermissionPolicy
        .permissions_for_role(
            WORKSPACE_ROLE_OWNER
        )
    )

    for permission in (
        WorkspacePermission
    ):
        assert (
            permission.value
            in permissions
        )


def test_admin_can_manage_employees(
) -> None:
    assert (
        WorkspacePermissionPolicy
        .allows(
            role_key=(
                WORKSPACE_ROLE_ADMIN
            ),
            permission=(
                WorkspacePermission
                .EMPLOYEES_MANAGE
                .value
            ),
        )
    )


def test_admin_can_manage_attendance(
) -> None:
    assert (
        WorkspacePermissionPolicy
        .allows(
            role_key=(
                WORKSPACE_ROLE_ADMIN
            ),
            permission=(
                WorkspacePermission
                .ATTENDANCE_MANAGE
                .value
            ),
        )
    )


def test_member_can_view_employees(
) -> None:
    assert (
        WorkspacePermissionPolicy
        .allows(
            role_key=(
                WORKSPACE_ROLE_MEMBER
            ),
            permission=(
                WorkspacePermission
                .EMPLOYEES_VIEW
                .value
            ),
        )
    )


def test_member_cannot_manage_employees(
) -> None:
    assert not (
        WorkspacePermissionPolicy
        .allows(
            role_key=(
                WORKSPACE_ROLE_MEMBER
            ),
            permission=(
                WorkspacePermission
                .EMPLOYEES_MANAGE
                .value
            ),
        )
    )


def test_member_cannot_view_live_monitoring(
) -> None:
    assert not (
        WorkspacePermissionPolicy
        .allows(
            role_key=(
                WORKSPACE_ROLE_MEMBER
            ),
            permission=(
                WorkspacePermission
                .MONITORING_LIVE_VIEW
                .value
            ),
        )
    )


def test_member_can_create_meeting(
) -> None:
    assert (
        WorkspacePermissionPolicy
        .allows(
            role_key=(
                WORKSPACE_ROLE_MEMBER
            ),
            permission=(
                WorkspacePermission
                .MEETINGS_CREATE
                .value
            ),
        )
    )


def test_unknown_role_has_no_permissions(
) -> None:
    assert (
        WorkspacePermissionPolicy
        .permissions_for_role(
            "unknown"
        )
        == frozenset()
    )


def test_none_role_has_no_permissions(
) -> None:
    assert (
        WorkspacePermissionPolicy
        .permissions_for_role(
            None
        )
        == frozenset()
    )