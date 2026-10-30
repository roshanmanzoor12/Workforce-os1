import asyncio
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.core.exceptions import ResourceNotFound
from app.modules.workspace_permissions import effective
from app.modules.workspace_permissions.permissions import (
    ALL_WORKSPACE_PERMISSIONS,
)
from app.modules.workspace_permissions.policy import (
    WorkspacePermissionPolicy,
)
from app.modules.workspace_permissions.service import (
    WorkspacePermissionService,
)


WORKSPACE_ID = uuid.uuid4()
MEMBERSHIP_ID = uuid.uuid4()


def membership(role_key="custom_reader"):
    return SimpleNamespace(
        id=MEMBERSHIP_ID,
        workspace_id=WORKSPACE_ID,
        status="active",
        role_key=role_key,
    )


def custom_role(role_key="custom_reader", **overrides):
    values = {
        "id": uuid.uuid4(),
        "workspace_id": WORKSPACE_ID,
        "role_key": role_key,
        "is_active": True,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def assignment(role_key, custom_role_id=None, **overrides):
    values = {
        "membership_id": MEMBERSHIP_ID,
        "role_key": role_key,
        "custom_role_id": custom_role_id,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def repository_fixture(monkeypatch):
    repository = SimpleNamespace(
        get_moderation=AsyncMock(return_value=None),
        get_custom_role_by_key=AsyncMock(return_value=None),
        get_role_permissions=AsyncMock(
            return_value=frozenset()
        ),
    )

    assignments = SimpleNamespace(
        list_for=AsyncMock(return_value=[]),
    )

    monkeypatch.setattr(
        effective,
        "WorkspaceRBACRepository",
        lambda session: repository,
    )
    monkeypatch.setattr(
        effective,
        "MembershipRoleAssignmentRepository",
        lambda session: assignments,
    )

    return repository, assignments


def resolve_access(member):
    return asyncio.run(
        effective.resolve_membership_access(
            object(),
            workspace_id=WORKSPACE_ID,
            membership=member,
        )
    )


def resolve(member):
    return asyncio.run(
        effective.resolve_membership_permissions(
            object(),
            workspace_id=WORKSPACE_ID,
            membership=member,
        )
    )


@pytest.mark.parametrize(
    "role_key",
    ["owner", "admin", "manager", "member", "client"],
)
def test_builtin_permissions_match_policy(monkeypatch, role_key):
    repository, _ = repository_fixture(monkeypatch)

    result = resolve(membership(role_key))

    assert result == (
        WorkspacePermissionPolicy.permissions_for_role(role_key)
    )
    repository.get_custom_role_by_key.assert_not_awaited()


def test_active_custom_role_loads_saved_permissions(monkeypatch):
    repository, _ = repository_fixture(monkeypatch)
    role = custom_role()

    repository.get_custom_role_by_key.return_value = role
    repository.get_role_permissions.return_value = frozenset(
        {"employees.read", "reports.self.read"}
    )

    access = resolve_access(membership())

    assert access.role_keys == ("custom_reader",)
    assert access.permissions == frozenset(
        {"employees.read", "reports.self.read"}
    )
    repository.get_custom_role_by_key.assert_awaited_once_with(
        workspace_id=WORKSPACE_ID,
        role_key="custom_reader",
    )
    repository.get_role_permissions.assert_awaited_once_with(
        role.id
    )


@pytest.mark.parametrize(
    "state",
    ["missing", "inactive", "foreign", "wrong_key"],
)
def test_unusable_custom_role_grants_nothing(monkeypatch, state):
    repository, _ = repository_fixture(monkeypatch)

    if state != "missing":
        role = custom_role()

        if state == "inactive":
            role.is_active = False
        elif state == "foreign":
            role.workspace_id = uuid.uuid4()
        elif state == "wrong_key":
            role.role_key = "another_role"

        repository.get_custom_role_by_key.return_value = role

    assert resolve(membership()) == frozenset()
    repository.get_role_permissions.assert_not_awaited()


def test_banned_member_is_rejected(monkeypatch):
    repository, assignments = repository_fixture(monkeypatch)
    repository.get_moderation.return_value = SimpleNamespace(
        is_banned=True
    )

    with pytest.raises(HTTPException) as error:
        resolve(membership("owner"))

    assert error.value.status_code == 403
    repository.get_custom_role_by_key.assert_not_awaited()
    assignments.list_for.assert_not_awaited()


@pytest.mark.parametrize(
    "invalid_state",
    ["inactive", "foreign", "invalid_id"],
)
def test_invalid_membership_is_rejected_before_role_lookup(
    monkeypatch,
    invalid_state,
):
    repository, assignments = repository_fixture(monkeypatch)
    member = membership()

    if invalid_state == "inactive":
        member.status = "removed"
    elif invalid_state == "foreign":
        member.workspace_id = uuid.uuid4()
    else:
        member.id = "invalid"

    with pytest.raises(ResourceNotFound):
        resolve(member)

    repository.get_moderation.assert_not_awaited()
    repository.get_custom_role_by_key.assert_not_awaited()
    assignments.list_for.assert_not_awaited()


def test_unknown_saved_permission_cannot_grant_access(monkeypatch):
    repository, _ = repository_fixture(monkeypatch)
    repository.get_custom_role_by_key.return_value = custom_role()
    repository.get_role_permissions.return_value = frozenset(
        {"employees.read", "phase38.unknown.permission"}
    )

    assert resolve(membership()) == frozenset({"employees.read"})


def test_builtin_additional_role_permissions_are_combined(monkeypatch):
    _, assignments = repository_fixture(monkeypatch)
    assignments.list_for.return_value = [
        assignment("manager"),
    ]

    access = resolve_access(membership("member"))

    expected = (
        WorkspacePermissionPolicy.permissions_for_role("member")
        | WorkspacePermissionPolicy.permissions_for_role("manager")
    )

    assert access.permissions == expected
    assert access.role_keys == ("manager", "member")
    assignments.list_for.assert_awaited_once_with(
        workspace_id=WORKSPACE_ID,
        membership_id=MEMBERSHIP_ID,
    )


def test_custom_additional_role_permissions_are_combined(monkeypatch):
    repository, assignments = repository_fixture(monkeypatch)
    role = custom_role("extra_reader")

    repository.get_custom_role_by_key.return_value = role
    repository.get_role_permissions.return_value = frozenset(
        {"employees.read", "phase38.unknown.permission"}
    )
    assignments.list_for.return_value = [
        assignment("extra_reader", role.id),
    ]

    access = resolve_access(membership("member"))

    expected = (
        WorkspacePermissionPolicy.permissions_for_role("member")
        | frozenset({"employees.read"})
    )

    assert access.permissions == expected
    assert access.role_keys == ("extra_reader", "member")
    assert "phase38.unknown.permission" not in access.permissions


@pytest.mark.parametrize(
    "state",
    ["inactive", "foreign", "stale_id", "missing_reference"],
)
def test_invalid_additional_custom_role_is_ignored(monkeypatch, state):
    repository, assignments = repository_fixture(monkeypatch)
    role = custom_role("extra_reader")
    reference = role.id

    if state == "inactive":
        role.is_active = False
    elif state == "foreign":
        role.workspace_id = uuid.uuid4()
    elif state == "stale_id":
        reference = uuid.uuid4()
    else:
        reference = None

    repository.get_custom_role_by_key.return_value = role
    assignments.list_for.return_value = [
        assignment("extra_reader", reference),
    ]

    access = resolve_access(membership("member"))

    assert access.role_keys == ("member",)
    assert access.permissions == (
        WorkspacePermissionPolicy.permissions_for_role("member")
    )
    repository.get_role_permissions.assert_not_awaited()


@pytest.mark.parametrize(
    "bad_assignment",
    [
        assignment("owner"),
        assignment("manager", uuid.uuid4()),
        assignment("manager", membership_id=uuid.uuid4()),
        assignment(" MANAGER "),
        assignment(""),
    ],
)
def test_malformed_additional_assignment_is_ignored(
    monkeypatch,
    bad_assignment,
):
    _, assignments = repository_fixture(monkeypatch)
    assignments.list_for.return_value = [bad_assignment]

    access = resolve_access(membership("member"))

    assert access.role_keys == ("member",)
    assert access.permissions == (
        WorkspacePermissionPolicy.permissions_for_role("member")
    )


def test_duplicate_additional_roles_are_deduplicated(monkeypatch):
    repository, assignments = repository_fixture(monkeypatch)
    role = custom_role("extra_reader")

    repository.get_custom_role_by_key.return_value = role
    repository.get_role_permissions.return_value = frozenset(
        {"employees.read"}
    )
    assignments.list_for.return_value = [
        assignment("extra_reader", role.id),
        assignment("extra_reader", role.id),
        assignment("member"),
    ]

    access = resolve_access(membership("member"))

    assert access.role_keys == ("extra_reader", "member")
    repository.get_role_permissions.assert_awaited_once_with(
        role.id
    )


def test_active_empty_custom_role_remains_in_role_list(monkeypatch):
    repository, assignments = repository_fixture(monkeypatch)
    role = custom_role("empty_role")

    repository.get_custom_role_by_key.return_value = role
    assignments.list_for.return_value = [
        assignment("empty_role", role.id),
    ]

    access = resolve_access(membership("member"))

    assert access.role_keys == ("empty_role", "member")
    assert access.permissions == (
        WorkspacePermissionPolicy.permissions_for_role("member")
    )


def test_owner_does_not_need_additional_assignment_lookup(monkeypatch):
    _, assignments = repository_fixture(monkeypatch)

    access = resolve_access(membership("owner"))

    assert access.role_keys == ("owner",)
    assert access.permissions == ALL_WORKSPACE_PERMISSIONS
    assignments.list_for.assert_not_awaited()


def test_empty_snapshot_does_not_restore_owner_permissions():
    service = WorkspacePermissionService(
        SimpleNamespace(
            role_key="owner",
            effective_permissions=frozenset(),
        )
    )

    assert service.list() == []
    assert not service.has("employees.read")

    with pytest.raises(HTTPException) as error:
        service.require("employees.read")

    assert error.value.status_code == 403


def test_snapshot_controls_all_permission_checks():
    service = WorkspacePermissionService(
        SimpleNamespace(
            role_key="owner",
            effective_permissions=frozenset({"employees.read"}),
        )
    )

    assert service.list() == ["employees.read"]
    assert service.has(" employees.read ")
    assert not service.has("reports.self.read")
    assert service.all({"employees.read"})
    assert not service.all(
        {"employees.read", "reports.self.read"}
    )
    assert service.any(
        {"employees.read", "reports.self.read"}
    )
    assert not service.any({"reports.self.read"})
    assert service.check_many(
        ["employees.read", "reports.self.read"]
    ) == {
        "employees.read": True,
        "reports.self.read": False,
    }


def test_invalid_snapshot_is_rejected():
    scope = SimpleNamespace(
        role_key="owner",
        effective_permissions=["employees.read"],
    )

    with pytest.raises(HTTPException) as error:
        WorkspacePermissionService(scope).list()

    assert error.value.status_code == 403


def test_unknown_snapshot_permission_is_filtered():
    service = WorkspacePermissionService(
        SimpleNamespace(
            role_key="owner",
            effective_permissions=frozenset(
                {"employees.read", "phase38.unknown.permission"}
            ),
        )
    )

    assert service.list() == ["employees.read"]
    assert not service.has("phase38.unknown.permission")


def test_legacy_role_only_scope_remains_compatible():
    service = WorkspacePermissionService(
        SimpleNamespace(role_key="owner")
    )

    assert set(service.list()) == set(ALL_WORKSPACE_PERMISSIONS)