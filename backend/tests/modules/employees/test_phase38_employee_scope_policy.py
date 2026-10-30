from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.modules.employees.scope_access import (
    build_employee_access,
    can_access_employee_row,
    require_employee_action,
    require_employee_read,
    require_employee_update_fields,
    require_employee_workspace_scope,
)


def make_access(permissions, *, role="member", employee=True):
    scope = SimpleNamespace(
        workspace_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        membership_id=uuid.uuid4(),
        role_key=role,
        effective_permissions=frozenset(permissions),
    )

    row = (
        SimpleNamespace(
            id=uuid.uuid4(),
            user_id=scope.user_id,
            team_id=uuid.uuid4(),
            department_id=uuid.uuid4(),
            is_active=True,
            employment_status="active",
        )
        if employee
        else None
    )

    return build_employee_access(scope, row), row


def test_self_permission_does_not_expose_another_employee():
    context, own = make_access({"employees.self.read"})

    other = SimpleNamespace(
        id=uuid.uuid4(),
        team_id=own.team_id,
        department_id=own.department_id,
    )

    assert can_access_employee_row(context, own)
    assert not can_access_employee_row(context, other)
    assert not context.is_workspace_scoped


def test_team_permission_uses_callers_actual_team():
    context, own = make_access({"employees.team.read"})

    teammate = SimpleNamespace(
        id=uuid.uuid4(),
        team_id=own.team_id,
    )

    unrelated = SimpleNamespace(
        id=uuid.uuid4(),
        team_id=uuid.uuid4(),
    )

    assert can_access_employee_row(context, teammate)
    assert not can_access_employee_row(context, unrelated)


def test_missing_team_does_not_grant_all_unassigned_employees():
    context, _ = make_access(
        {"employees.team.read"},
        employee=False,
    )

    assert not can_access_employee_row(
        context,
        SimpleNamespace(id=uuid.uuid4(), team_id=None),
    )


def test_all_read_is_an_explicit_workspace_grant():
    context, _ = make_access(
        {"employees.all.read"},
        employee=False,
    )

    assert context.is_workspace_scoped
    assert can_access_employee_row(
        context,
        SimpleNamespace(id=uuid.uuid4()),
    )


def test_management_permission_does_not_expand_scope():
    context, own = make_access({"employees.manage"})

    assert not context.is_workspace_scoped
    assert can_access_employee_row(context, own)

    with pytest.raises(HTTPException):
        require_employee_workspace_scope(context)


def test_empty_owner_snapshot_remains_empty():
    context, _ = make_access(set(), role="owner")

    assert context.permissions == frozenset()
    assert not context.is_workspace_scoped

    with pytest.raises(HTTPException):
        require_employee_read(context)


@pytest.mark.parametrize("action", ["create", "update", "delete"])
def test_action_permission_is_required(action):
    context, _ = make_access({"employees.all.read"})

    with pytest.raises(HTTPException) as error:
        require_employee_action(context, action)

    assert error.value.status_code == 403


@pytest.mark.parametrize("action", ["create", "update", "delete"])
def test_specific_action_permission_is_accepted(action):
    context, _ = make_access({f"employees.{action}"})
    require_employee_action(context, action)


@pytest.mark.parametrize(
    "field",
    [
        "user_id",
        "department_id",
        "team_id",
        "manager_id",
        "employment_status",
        "is_active",
        "employee_code",
        "work_email",
        "hire_date",
        "termination_date",
        "job_title",
    ],
)
def test_limited_scope_cannot_change_protected_fields(field):
    context, _ = make_access({"employees.update"})

    with pytest.raises(HTTPException):
        require_employee_update_fields(context, {field})


def test_limited_scope_can_change_profile_fields():
    context, _ = make_access({"employees.update"})

    require_employee_update_fields(
        context,
        {"first_name", "last_name", "phone_number", "avatar_url"},
    )


def test_workspace_scope_accepts_protected_fields():
    context, _ = make_access({
        "employees.all.read",
        "employees.update",
    })

    require_employee_update_fields(
        context,
        {"user_id", "team_id", "employment_status"},
    )


def test_mismatched_employee_identity_is_rejected():
    scope = SimpleNamespace(
        workspace_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        membership_id=uuid.uuid4(),
        role_key="member",
        effective_permissions=frozenset({"employees.self.read"}),
    )

    row = SimpleNamespace(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        is_active=True,
        employment_status="active",
    )

    with pytest.raises(HTTPException):
        build_employee_access(scope, row)