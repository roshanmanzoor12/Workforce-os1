from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest

from app.modules.workspace_permissions.access_context import (
    WorkspaceAccessContext,
)
from app.modules.workspace_permissions.scope_enforcement import (
    can_access_employee,
    can_access_monitoring,
    can_access_payroll,
    filter_by_scope,
)
from app.modules.workspace_permissions.scopes import (
    WorkspaceResourceScope,
    WorkspaceScopeType,
)


WORKSPACE_ID = uuid.uuid4()
USER_ID = uuid.uuid4()
EMPLOYEE_ID = uuid.uuid4()
TEAM_ID = uuid.uuid4()
DEPARTMENT_ID = uuid.uuid4()
COMPANY_ID = uuid.uuid4()


def make_context(
    scope_type: WorkspaceScopeType | None,
) -> WorkspaceAccessContext:
    resource_ids = {
        WorkspaceScopeType.TEAM: TEAM_ID,
        WorkspaceScopeType.DEPARTMENT: DEPARTMENT_ID,
        WorkspaceScopeType.COMPANY: COMPANY_ID,
    }

    scopes = (
        ()
        if scope_type is None
        else (
            WorkspaceResourceScope(
                type=scope_type,
                id=resource_ids.get(scope_type),
            ),
        )
    )

    return WorkspaceAccessContext(
        user_id=USER_ID,
        workspace_id=WORKSPACE_ID,
        membership_id=uuid.uuid4(),
        employee_id=EMPLOYEE_ID,
        role_key="member",
        permissions=frozenset({"employees.self.read"}),
        scopes=scopes,
        team_ids=frozenset({TEAM_ID}),
        department_ids=frozenset({DEPARTMENT_ID}),
        company_ids=frozenset({COMPANY_ID}),
    )


@pytest.mark.parametrize(
    "scope_type",
    [
        WorkspaceScopeType.TEAM,
        WorkspaceScopeType.DEPARTMENT,
        WorkspaceScopeType.COMPANY,
        WorkspaceScopeType.SHARED,
    ],
)
def test_resource_scope_requires_id(scope_type) -> None:
    with pytest.raises(ValueError):
        WorkspaceResourceScope(type=scope_type)


@pytest.mark.parametrize(
    "scope_type",
    [
        WorkspaceScopeType.SELF,
        WorkspaceScopeType.WORKSPACE,
    ],
)
def test_global_scope_rejects_id(scope_type) -> None:
    with pytest.raises(ValueError):
        WorkspaceResourceScope(
            type=scope_type,
            id=uuid.uuid4(),
        )


def test_self_employee_uses_employee_identity() -> None:
    employee = SimpleNamespace(
        id=EMPLOYEE_ID,
        workspace_id=WORKSPACE_ID,
    )

    assert can_access_employee(
        employee,
        make_context(WorkspaceScopeType.SELF),
        WorkspaceScopeType.SELF,
    )


@pytest.mark.parametrize(
    "access_check",
    [can_access_payroll, can_access_monitoring],
)
def test_self_records_use_employee_identity(access_check) -> None:
    record = SimpleNamespace(
        employee_id=EMPLOYEE_ID,
        workspace_id=WORKSPACE_ID,
    )

    assert access_check(
        record,
        make_context(WorkspaceScopeType.SELF),
        WorkspaceScopeType.SELF,
    )


def test_self_denies_another_employee() -> None:
    employee = SimpleNamespace(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        workspace_id=WORKSPACE_ID,
    )

    assert not can_access_employee(
        employee,
        make_context(WorkspaceScopeType.SELF),
        WorkspaceScopeType.SELF,
    )


@pytest.mark.parametrize(
    ("scope_type", "field", "resource_id"),
    [
        (WorkspaceScopeType.TEAM, "team_id", TEAM_ID),
        (
            WorkspaceScopeType.DEPARTMENT,
            "department_id",
            DEPARTMENT_ID,
        ),
        (WorkspaceScopeType.COMPANY, "company_id", COMPANY_ID),
    ],
)
def test_filters_assigned_resources(
    scope_type,
    field,
    resource_id,
) -> None:
    permitted = {
        "workspace_id": WORKSPACE_ID,
        field: resource_id,
    }
    unrelated = {
        "workspace_id": WORKSPACE_ID,
        field: uuid.uuid4(),
    }

    assert filter_by_scope(
        [permitted, unrelated],
        make_context(scope_type),
        scope_type,
    ) == [permitted]


def test_cross_workspace_denied() -> None:
    employee = SimpleNamespace(
        id=EMPLOYEE_ID,
        user_id=USER_ID,
        workspace_id=uuid.uuid4(),
    )

    assert not can_access_employee(
        employee,
        make_context(WorkspaceScopeType.WORKSPACE),
        WorkspaceScopeType.WORKSPACE,
    )


def test_missing_workspace_denied() -> None:
    employee = SimpleNamespace(
        id=EMPLOYEE_ID,
        user_id=USER_ID,
    )

    assert not can_access_employee(
        employee,
        make_context(WorkspaceScopeType.WORKSPACE),
        WorkspaceScopeType.WORKSPACE,
    )


def test_missing_scope_denies_access() -> None:
    employee = SimpleNamespace(
        id=uuid.uuid4(),
        workspace_id=WORKSPACE_ID,
    )

    assert not can_access_employee(
        employee,
        make_context(None),
    )


def test_default_self_scope_denies_other_employee() -> None:
    employee = SimpleNamespace(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        workspace_id=WORKSPACE_ID,
    )

    assert not can_access_employee(
        employee,
        make_context(WorkspaceScopeType.SELF),
    )


def test_requested_workspace_cannot_expand_self_grant() -> None:
    employee = SimpleNamespace(
        id=uuid.uuid4(),
        workspace_id=WORKSPACE_ID,
    )

    assert not can_access_employee(
        employee,
        make_context(WorkspaceScopeType.SELF),
        WorkspaceScopeType.WORKSPACE,
    )
