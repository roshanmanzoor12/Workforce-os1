from __future__ import annotations

from app.modules.workspace_invitations.enums import (
    WorkspaceInvitationStatus,
)
from app.modules.workspace_invitations.security import (
    generate_invitation_token,
    hash_invitation_token,
    invitation_token_matches,
    normalize_invitation_email,
)
from app.modules.workspace_permissions.permissions import (
    WorkspacePermission,
)
from app.modules.workspace_permissions.policy import (
    WorkspacePermissionPolicy,
)
from app.modules.workspace_permissions.roles import (
    ADMIN_ROLE,
    CLIENT_ROLE,
    MANAGER_ROLE,
    MEMBER_ROLE,
    OWNER_ROLE,
)
from app.modules.workspace_permissions.scopes import (
    WorkspaceScopeType,
    self_scope,
    workspace_scope,
)


def test_builtin_roles() -> None:
    assert {
        OWNER_ROLE,
        ADMIN_ROLE,
        MANAGER_ROLE,
        MEMBER_ROLE,
        CLIENT_ROLE,
    } == {
        "owner",
        "admin",
        "manager",
        "member",
        "client",
    }


def test_owner_has_every_registered_permission() -> None:
    assert (
        WorkspacePermissionPolicy
        .allows(
            role_key=OWNER_ROLE,
            permission=(
                WorkspacePermission
                .BILLING_MANAGE
                .value
            ),
        )
    )

    assert (
        WorkspacePermissionPolicy
        .allows(
            role_key=OWNER_ROLE,
            permission=(
                WorkspacePermission
                .ROLES_MANAGE
                .value
            ),
        )
    )


def test_admin_does_not_get_owner_sensitive_defaults() -> None:
    assert not (
        WorkspacePermissionPolicy
        .allows(
            role_key=ADMIN_ROLE,
            permission=(
                WorkspacePermission
                .BILLING_MANAGE
                .value
            ),
        )
    )

    assert not (
        WorkspacePermissionPolicy
        .allows(
            role_key=ADMIN_ROLE,
            permission=(
                WorkspacePermission
                .ROLES_MANAGE
                .value
            ),
        )
    )


def test_manager_team_access() -> None:
    assert (
        WorkspacePermissionPolicy
        .allows(
            role_key=MANAGER_ROLE,
            permission=(
                WorkspacePermission
                .ATTENDANCE_TEAM_READ
                .value
            ),
        )
    )

    assert not (
        WorkspacePermissionPolicy
        .allows(
            role_key=MANAGER_ROLE,
            permission=(
                WorkspacePermission
                .PAYROLL_READ
                .value
            ),
        )
    )


def test_member_self_access() -> None:
    assert (
        WorkspacePermissionPolicy
        .allows(
            role_key=MEMBER_ROLE,
            permission=(
                WorkspacePermission
                .ATTENDANCE_SELF_READ
                .value
            ),
        )
    )

    assert not (
        WorkspacePermissionPolicy
        .allows(
            role_key=MEMBER_ROLE,
            permission=(
                WorkspacePermission
                .ATTENDANCE_ALL_READ
                .value
            ),
        )
    )


def test_client_has_no_employee_or_monitoring_access() -> None:
    assert not (
        WorkspacePermissionPolicy
        .allows(
            role_key=CLIENT_ROLE,
            permission=(
                WorkspacePermission
                .EMPLOYEES_ALL_READ
                .value
            ),
        )
    )

    assert not (
        WorkspacePermissionPolicy
        .allows(
            role_key=CLIENT_ROLE,
            permission=(
                WorkspacePermission
                .MONITORING_SELF_READ
                .value
            ),
        )
    )


def test_legacy_permissions_remain_supported() -> None:
    assert (
        WorkspacePermissionPolicy
        .allows(
            role_key=MEMBER_ROLE,
            permission=(
                WorkspacePermission
                .GOALS_SELF
                .value
            ),
        )
    )

    assert (
        WorkspacePermissionPolicy
        .allows(
            role_key=ADMIN_ROLE,
            permission=(
                WorkspacePermission
                .EMPLOYEES_MANAGE
                .value
            ),
        )
    )


def test_scope_helpers() -> None:
    own = self_scope()

    assert (
        own.type
        == WorkspaceScopeType.SELF
    )

    whole_workspace = (
        workspace_scope()
    )

    assert (
        whole_workspace.type
        == (
            WorkspaceScopeType
            .WORKSPACE
        )
    )


def test_invitation_email_normalization() -> None:
    assert (
        normalize_invitation_email(
            "  Test@Example.COM "
        )
        == "test@example.com"
    )


def test_invitation_token_hashing() -> None:
    token = (
        generate_invitation_token()
    )

    token_hash = (
        hash_invitation_token(
            token
        )
    )

    assert token != token_hash

    assert (
        invitation_token_matches(
            token=token,
            token_hash=token_hash,
        )
    )


def test_invitation_statuses() -> None:
    assert {
        item.value
        for item
        in WorkspaceInvitationStatus
    } == {
        "pending",
        "accepted",
        "declined",
        "expired",
        "revoked",
    }