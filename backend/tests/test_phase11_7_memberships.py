from __future__ import annotations

import uuid

from app.modules.memberships.enums import (
    WorkspaceMembershipRole,
    WorkspaceMembershipSource,
    WorkspaceMembershipStatus,
)
from app.modules.memberships.models import (
    WorkspaceMembership,
)
from app.modules.memberships.schemas import (
    WorkspaceMembershipCreateRequest,
    WorkspaceMembershipRoleRequest,
)
from app.modules.memberships.service import (
    MANAGER_ROLES,
    WORKSPACE_ADMIN_ROLES,
)


def test_membership_role_values() -> None:
    assert (
        WorkspaceMembershipRole.OWNER.value
        == "OWNER"
    )

    assert (
        WorkspaceMembershipRole.ADMIN.value
        == "ADMIN"
    )

    assert (
        WorkspaceMembershipRole.MANAGER.value
        == "MANAGER"
    )

    assert (
        WorkspaceMembershipRole.MEMBER.value
        == "MEMBER"
    )


def test_membership_status_values() -> None:
    assert (
        WorkspaceMembershipStatus.INVITED.value
        == "INVITED"
    )

    assert (
        WorkspaceMembershipStatus.ACTIVE.value
        == "ACTIVE"
    )

    assert (
        WorkspaceMembershipStatus.SUSPENDED.value
        == "SUSPENDED"
    )

    assert (
        WorkspaceMembershipStatus.REMOVED.value
        == "REMOVED"
    )


def test_membership_source_values() -> None:
    assert (
        WorkspaceMembershipSource.CREATOR.value
        == "CREATOR"
    )

    assert (
        WorkspaceMembershipSource.INVITATION.value
        == "INVITATION"
    )

    assert (
        WorkspaceMembershipSource.ADMIN.value
        == "ADMIN"
    )


def test_owner_can_manage_members() -> None:
    assert (
        WorkspaceMembershipRole.OWNER
        in MANAGER_ROLES
    )


def test_admin_can_manage_members() -> None:
    assert (
        WorkspaceMembershipRole.ADMIN
        in MANAGER_ROLES
    )


def test_manager_cannot_manage_members() -> None:
    assert (
        WorkspaceMembershipRole.MANAGER
        not in MANAGER_ROLES
    )


def test_owner_is_workspace_admin() -> None:
    assert (
        WorkspaceMembershipRole.OWNER
        in WORKSPACE_ADMIN_ROLES
    )


def test_admin_is_not_workspace_owner() -> None:
    assert (
        WorkspaceMembershipRole.ADMIN
        not in WORKSPACE_ADMIN_ROLES
    )


def test_create_request_defaults_member() -> None:
    request = (
        WorkspaceMembershipCreateRequest(
            user_id=uuid.uuid4()
        )
    )

    assert (
        request.role
        == WorkspaceMembershipRole.MEMBER
    )


def test_role_request_accepts_admin() -> None:
    request = (
        WorkspaceMembershipRoleRequest(
            role=(
                WorkspaceMembershipRole.ADMIN
            )
        )
    )

    assert (
        request.role
        == WorkspaceMembershipRole.ADMIN
    )


def test_membership_table_name() -> None:
    assert (
        WorkspaceMembership.__tablename__
        == "workspace_memberships"
    )


def test_membership_required_columns() -> None:
    columns = {
        column.name
        for column
        in (
            WorkspaceMembership
            .__table__
            .columns
        )
    }

    expected = {
        "id",
        "workspace_id",
        "user_id",
        "role",
        "status",
        "source",
        "invited_by_user_id",
        "activated_at",
        "suspended_at",
        "removed_at",
        "created_at",
        "updated_at",
    }

    assert expected.issubset(
        columns
    )