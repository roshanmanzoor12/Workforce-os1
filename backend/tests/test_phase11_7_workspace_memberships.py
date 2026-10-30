from __future__ import annotations

import uuid

from app.modules.memberships.enums import (
    WorkspaceMembershipRole,
    WorkspaceMembershipStatus,
)
from app.modules.memberships.models import (
    WorkspaceMembership,
)
from app.modules.memberships.schemas import (
    WorkspaceMembershipAccessResponse,
    WorkspaceMembershipCreateRequest,
    WorkspaceMembershipRoleUpdateRequest,
)


def test_reuses_existing_workspace_membership_model(
) -> None:
    assert (
        WorkspaceMembership.__module__
        == "app.modules.workspaces.models"
    )

    assert (
        WorkspaceMembership.__tablename__
        == "workspace_memberships"
    )


def test_membership_role_values() -> None:
    assert (
        WorkspaceMembershipRole.OWNER.value
        == "owner"
    )

    assert (
        WorkspaceMembershipRole.ADMIN.value
        == "admin"
    )

    assert (
        WorkspaceMembershipRole.MEMBER.value
        == "member"
    )


def test_membership_status_values() -> None:
    assert (
        WorkspaceMembershipStatus.INVITED.value
        == "invited"
    )

    assert (
        WorkspaceMembershipStatus.ACTIVE.value
        == "active"
    )

    assert (
        WorkspaceMembershipStatus.SUSPENDED.value
        == "suspended"
    )

    assert (
        WorkspaceMembershipStatus.REMOVED.value
        == "removed"
    )


def test_create_defaults_to_member() -> None:
    request = (
        WorkspaceMembershipCreateRequest()
    )

    assert (
        request.role
        == WorkspaceMembershipRole.MEMBER
    )


def test_create_admin_membership() -> None:
    request = (
        WorkspaceMembershipCreateRequest(
            role=(
                WorkspaceMembershipRole.ADMIN
            )
        )
    )

    assert (
        request.role
        == WorkspaceMembershipRole.ADMIN
    )


def test_role_update_owner() -> None:
    request = (
        WorkspaceMembershipRoleUpdateRequest(
            role=(
                WorkspaceMembershipRole.OWNER
            )
        )
    )

    assert (
        request.role
        == WorkspaceMembershipRole.OWNER
    )


def test_access_response_member() -> None:
    response = (
        WorkspaceMembershipAccessResponse(
            workspace_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            is_member=True,
            role=(
                WorkspaceMembershipRole.MEMBER
            ),
            status=(
                WorkspaceMembershipStatus.ACTIVE
            ),
            can_manage_members=False,
        )
    )

    assert response.is_member is True

    assert (
        response.can_manage_members
        is False
    )


def test_access_response_owner_manager() -> None:
    response = (
        WorkspaceMembershipAccessResponse(
            workspace_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            is_member=True,
            role=(
                WorkspaceMembershipRole.OWNER
            ),
            status=(
                WorkspaceMembershipStatus.ACTIVE
            ),
            can_manage_members=True,
        )
    )

    assert (
        response.can_manage_members
        is True
    )


def test_existing_model_has_real_columns() -> None:
    columns = {
        column.name
        for column
        in WorkspaceMembership.__table__.columns
    }

    required = {
        "id",
        "workspace_id",
        "user_id",
        "role_key",
        "status",
        "invited_by_user_id",
        "invited_at",
        "joined_at",
        "suspended_at",
        "removed_at",
        "created_at",
        "updated_at",
    }

    assert required.issubset(
        columns
    )