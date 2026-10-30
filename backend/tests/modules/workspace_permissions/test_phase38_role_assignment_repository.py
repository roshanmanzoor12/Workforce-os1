import asyncio
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from app.core.exceptions import ResourceNotFound, ValidationError
from app.modules.workspace_rbac.assignment_repository import (
    MembershipRoleAssignmentRepository,
)


WORKSPACE_ID = uuid.uuid4()
MEMBERSHIP_ID = uuid.uuid4()
ACTOR_ID = uuid.uuid4()


def member(**changes):
    values = {
        "id": MEMBERSHIP_ID,
        "workspace_id": WORKSPACE_ID,
        "status": "active",
        "role_key": "member",
    }
    values.update(changes)
    return SimpleNamespace(**values)


def session_with(*results):
    return SimpleNamespace(
        scalar=AsyncMock(side_effect=list(results)),
        execute=AsyncMock(),
        add=Mock(),
        delete=AsyncMock(),
        flush=AsyncMock(),
        commit=AsyncMock(),
    )


def add_role(repository, role_key):
    return asyncio.run(
        repository.add(
            workspace_id=WORKSPACE_ID,
            membership_id=MEMBERSHIP_ID,
            role_key=role_key,
            granted_by_user_id=ACTOR_ID,
        )
    )


@pytest.mark.parametrize("role_key", ["owner", " OWNER "])
def test_additional_owner_is_rejected_before_database_access(
    role_key,
):
    session = session_with()
    repository = MembershipRoleAssignmentRepository(session)

    with pytest.raises(ValidationError):
        add_role(repository, role_key)

    session.scalar.assert_not_awaited()
    session.add.assert_not_called()


@pytest.mark.parametrize(
    "target",
    [
        None,
        member(workspace_id=uuid.uuid4()),
        member(status="removed"),
    ],
)
def test_missing_foreign_or_inactive_membership_cannot_receive_role(
    target,
):
    session = session_with(target)
    repository = MembershipRoleAssignmentRepository(session)

    with pytest.raises(ResourceNotFound):
        add_role(repository, "manager")

    session.add.assert_not_called()
    session.flush.assert_not_awaited()


def test_primary_role_is_not_duplicated():
    session = session_with(member())
    repository = MembershipRoleAssignmentRepository(session)

    with pytest.raises(ValidationError):
        add_role(repository, "member")

    session.add.assert_not_called()


@pytest.mark.parametrize(
    "custom_role",
    [
        None,
        SimpleNamespace(
            id=uuid.uuid4(),
            workspace_id=uuid.uuid4(),
            role_key="custom_reader",
            is_active=True,
        ),
        SimpleNamespace(
            id=uuid.uuid4(),
            workspace_id=WORKSPACE_ID,
            role_key="custom_reader",
            is_active=False,
        ),
    ],
)
def test_unusable_custom_role_cannot_be_assigned(custom_role):
    session = session_with(member(), custom_role)
    repository = MembershipRoleAssignmentRepository(session)

    with pytest.raises(ResourceNotFound):
        add_role(repository, "custom_reader")

    session.add.assert_not_called()


def test_builtin_assignment_is_created_without_committing():
    session = session_with(member(), None)
    repository = MembershipRoleAssignmentRepository(session)

    assignment = add_role(repository, " MANAGER ")

    assert assignment.membership_id == MEMBERSHIP_ID
    assert assignment.role_key == "manager"
    assert assignment.custom_role_id is None
    assert assignment.granted_by_user_id == ACTOR_ID

    session.add.assert_called_once_with(assignment)
    session.flush.assert_awaited_once()
    session.commit.assert_not_awaited()


def test_existing_assignment_is_idempotent():
    existing = SimpleNamespace(
        membership_id=MEMBERSHIP_ID,
        role_key="manager",
        custom_role_id=None,
    )
    session = session_with(member(), existing)
    repository = MembershipRoleAssignmentRepository(session)

    assert add_role(repository, "manager") is existing
    session.add.assert_not_called()
    session.flush.assert_not_awaited()


def test_custom_assignment_references_the_validated_role():
    custom_role = SimpleNamespace(
        id=uuid.uuid4(),
        workspace_id=WORKSPACE_ID,
        role_key="custom_reader",
        is_active=True,
    )
    session = session_with(member(), custom_role, None)
    repository = MembershipRoleAssignmentRepository(session)

    assignment = add_role(repository, "custom_reader")

    assert assignment.custom_role_id == custom_role.id
    assert assignment.role_key == "custom_reader"
    session.commit.assert_not_awaited()


def test_remove_missing_assignment_is_idempotent():
    session = session_with(member(), None)
    repository = MembershipRoleAssignmentRepository(session)

    removed = asyncio.run(
        repository.remove(
            workspace_id=WORKSPACE_ID,
            membership_id=MEMBERSHIP_ID,
            role_key="manager",
        )
    )

    assert removed is False
    session.delete.assert_not_awaited()


def test_remove_foreign_membership_is_rejected():
    session = session_with(
        member(workspace_id=uuid.uuid4())
    )
    repository = MembershipRoleAssignmentRepository(session)

    with pytest.raises(ResourceNotFound):
        asyncio.run(
            repository.remove(
                workspace_id=WORKSPACE_ID,
                membership_id=MEMBERSHIP_ID,
                role_key="manager",
            )
        )

    session.delete.assert_not_awaited()