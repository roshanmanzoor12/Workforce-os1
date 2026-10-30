from __future__ import annotations

import uuid
from types import SimpleNamespace

from app.modules.workspace_permissions.access_context import (
    WorkspaceAccessContext,
)
from app.modules.workspace_permissions.scope_enforcement import (
    can_access_employee,
    can_access_monitoring,
    can_access_payroll,
    filter_by_scope,
    resolve_permission_scope,
)
from app.modules.workspace_permissions.scopes import (
    WorkspaceScopeType,
    WorkspaceResourceScope,
)


WORKSPACE_ID = uuid.uuid4()
USER_ID = uuid.uuid4()
OTHER_USER_ID = uuid.uuid4()
COMPANY_ID = uuid.uuid4()
DEPARTMENT_ID = uuid.uuid4()
TEAM_ID = uuid.uuid4()
OTHER_TEAM_ID = uuid.uuid4()


def context() -> WorkspaceAccessContext:
    return WorkspaceAccessContext(
        user_id=USER_ID,
        workspace_id=WORKSPACE_ID,
        membership_id=uuid.uuid4(),
        scopes=(
            WorkspaceResourceScope(
                WorkspaceScopeType.SELF
            ),
            WorkspaceResourceScope(
                WorkspaceScopeType.TEAM,
                TEAM_ID,
            ),
            WorkspaceResourceScope(
                WorkspaceScopeType.DEPARTMENT,
                DEPARTMENT_ID,
            ),
            WorkspaceResourceScope(
                WorkspaceScopeType.COMPANY,
                COMPANY_ID,
            ),
            WorkspaceResourceScope(
                WorkspaceScopeType.WORKSPACE
            ),
        ),
        company_ids=frozenset({COMPANY_ID}),
        department_ids=frozenset({DEPARTMENT_ID}),
        team_ids=frozenset({TEAM_ID}),
    )


def test_phase25_resolves_permission_scope() -> None:
    assert (
        resolve_permission_scope(
            "employees.self.read"
        )
        == WorkspaceScopeType.SELF
    )

    assert (
        resolve_permission_scope(
            "employees.team.read"
        )
        == WorkspaceScopeType.TEAM
    )

    assert (
        resolve_permission_scope(
            "employees.department.read"
        )
        == WorkspaceScopeType.DEPARTMENT
    )

    assert (
        resolve_permission_scope(
            "payroll.company.read"
        )
        == WorkspaceScopeType.COMPANY
    )

    assert (
        resolve_permission_scope(
            "workspace.manage"
        )
        == WorkspaceScopeType.WORKSPACE
    )


def test_phase25_filters_self_scope() -> None:
    items = [
        SimpleNamespace(
            id=USER_ID,
            user_id=USER_ID,
            workspace_id=WORKSPACE_ID,
        ),
        SimpleNamespace(
            id=OTHER_USER_ID,
            user_id=OTHER_USER_ID,
            workspace_id=WORKSPACE_ID,
        ),
    ]

    result = filter_by_scope(
        items,
        context(),
        WorkspaceScopeType.SELF,
    )

    assert len(result) == 1
    assert result[0].user_id == USER_ID


def test_phase25_filters_team_scope() -> None:
    items = [
        SimpleNamespace(
            team_id=TEAM_ID,
            workspace_id=WORKSPACE_ID,
        ),
        SimpleNamespace(
            team_id=OTHER_TEAM_ID,
            workspace_id=WORKSPACE_ID,
        ),
    ]

    result = filter_by_scope(
        items,
        context(),
        WorkspaceScopeType.TEAM,
    )

    assert len(result) == 1
    assert result[0].team_id == TEAM_ID


def test_phase25_rejects_wrong_workspace() -> None:
    item = SimpleNamespace(
        user_id=USER_ID,
        workspace_id=uuid.uuid4(),
    )

    assert not can_access_employee(
        item,
        context(),
        WorkspaceScopeType.SELF,
    )


def test_phase25_employee_access_uses_scope() -> None:
    employee = SimpleNamespace(
        id=USER_ID,
        user_id=USER_ID,
        workspace_id=WORKSPACE_ID,
    )

    assert can_access_employee(
        employee,
        context(),
        WorkspaceScopeType.SELF,
    )


def test_phase25_payroll_access_uses_scope() -> None:
    payroll = SimpleNamespace(
        employee_id=USER_ID,
        workspace_id=WORKSPACE_ID,
    )

    assert can_access_payroll(
        payroll,
        context(),
        WorkspaceScopeType.SELF,
    )


def test_phase25_monitoring_access_uses_scope() -> None:
    monitoring = SimpleNamespace(
        employee_id=USER_ID,
        workspace_id=WORKSPACE_ID,
    )

    assert can_access_monitoring(
        monitoring,
        context(),
        WorkspaceScopeType.SELF,
    )