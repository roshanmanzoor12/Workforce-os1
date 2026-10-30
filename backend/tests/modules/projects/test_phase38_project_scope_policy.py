from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.dialects import postgresql

from app.modules.projects.access import (
    employee_scope_predicate,
    project_scope_predicate,
    require_project_context,
    resolve_project_access,
    validate_context_identity,
)
from app.modules.workspace_permissions.access_context import (
    WorkspaceAccessContext,
)
from app.modules.workspace_permissions.scopes import (
    WorkspaceResourceScope,
    WorkspaceScopeType,
    department_scope,
    self_scope,
    team_scope,
    workspace_scope,
)


def context(*grants, employee_id=None, permissions=None):
    return WorkspaceAccessContext(
        user_id=uuid4(),
        workspace_id=uuid4(),
        membership_id=uuid4(),
        employee_id=employee_id,
        role_key="member",
        permissions=(
            frozenset({"projects.view"})
            if permissions is None
            else permissions
        ),
        scopes=grants,
    )


def compiled(expression):
    return expression.compile(
        dialect=postgresql.dialect(),
        compile_kwargs={"literal_binds": True},
    )


def test_workspace_scope_allows_all_project_rows():
    result = str(compiled(project_scope_predicate(context(workspace_scope()))))
    assert result == "true"


def test_missing_scopes_do_not_become_workspace_access():
    result = str(compiled(project_scope_predicate(context())))
    assert "false" in result
    assert "owner_employee_id IN" in result


def test_self_scope_filters_through_employee_identity():
    employee_id = uuid4()
    result = str(
        compiled(
            project_scope_predicate(
                context(self_scope(), employee_id=employee_id)
            )
        )
    )

    assert "owner_employee_id IN" in result
    assert "employees.id =" in result
    assert str(employee_id) in result
    assert "employees.is_active IS true" in result
    assert "employees.employment_status" in result


def test_missing_self_employee_mapping_denies_access():
    result = str(
        compiled(project_scope_predicate(context(self_scope())))
    )
    assert "false" in result


@pytest.mark.parametrize(
    "factory,column",
    [
        (team_scope, "employees.team_id"),
        (department_scope, "employees.department_id"),
    ],
)
def test_organization_grants_use_matching_namespace(factory, column):
    resource_id = uuid4()
    result = str(
        compiled(employee_scope_predicate(context(factory(resource_id))))
    )
    assert column in result
    assert str(resource_id) in result


def test_shared_grant_matches_project_id_only():
    project_id = uuid4()
    grant = WorkspaceResourceScope(
        type=WorkspaceScopeType.SHARED,
        id=project_id,
    )

    result = str(compiled(project_scope_predicate(context(grant))))

    assert "projects.id IN" in result
    assert str(project_id) in result
    assert str(compiled(employee_scope_predicate(context(grant)))) == "false"


def test_company_scope_is_denied_for_model_without_company_column():
    grant = WorkspaceResourceScope(
        type=WorkspaceScopeType.COMPANY,
        id=uuid4(),
    )
    result = str(compiled(employee_scope_predicate(context(grant))))
    assert result == "false"


def test_permission_is_required_even_with_workspace_scope():
    access = context(workspace_scope(), permissions=frozenset())

    with pytest.raises(HTTPException) as error:
        require_project_context(access)

    assert error.value.status_code == 403


def test_read_permission_does_not_grant_management():
    access = context(workspace_scope())

    with pytest.raises(HTTPException) as error:
        require_project_context(access, manage=True)

    assert error.value.status_code == 403


def test_foreign_context_identity_is_rejected():
    access = context(self_scope())
    scope = SimpleNamespace(
        workspace_id=uuid4(),
        user_id=access.user_id,
        membership_id=access.membership_id,
    )

    with pytest.raises(HTTPException) as error:
        validate_context_identity(scope, access)

    assert error.value.status_code == 403


def make_scope(role_key="member", permissions=None, employee_ids=None):
    session = SimpleNamespace(
        scalars=AsyncMock(
            return_value=SimpleNamespace(
                all=lambda: list(employee_ids or [])
            )
        )
    )

    return SimpleNamespace(
        workspace_id=uuid4(),
        user_id=uuid4(),
        membership_id=uuid4(),
        role_key=role_key,
        effective_permissions=(
            frozenset({"projects.view"})
            if permissions is None
            else permissions
        ),
        session=session,
    )


@pytest.mark.asyncio
async def test_member_defaults_to_self_scope():
    employee_id = uuid4()
    scope = make_scope(employee_ids=[employee_id])

    result = await resolve_project_access(scope)

    assert result.employee_id == employee_id
    assert result.has_scope(WorkspaceScopeType.SELF)
    assert not result.is_workspace_scoped
    validate_context_identity(scope, result)


@pytest.mark.asyncio
async def test_custom_management_permission_does_not_expand_scope():
    scope = make_scope(
        role_key="custom_manager",
        permissions=frozenset({"projects.view", "projects.manage"}),
    )

    result = await resolve_project_access(scope)

    assert result.has_permission("projects.manage")
    assert result.has_scope(WorkspaceScopeType.SELF)
    assert not result.is_workspace_scoped


@pytest.mark.asyncio
async def test_empty_owner_snapshot_does_not_restore_permissions():
    scope = make_scope(role_key="owner", permissions=frozenset())

    result = await resolve_project_access(scope)

    assert result.permissions == frozenset()

    with pytest.raises(HTTPException):
        require_project_context(result)


@pytest.mark.asyncio
async def test_admin_with_permission_retains_workspace_scope():
    result = await resolve_project_access(make_scope(role_key="admin"))
    assert result.is_workspace_scoped


@pytest.mark.asyncio
async def test_ambiguous_employee_mapping_is_rejected():
    scope = make_scope(employee_ids=[uuid4(), uuid4()])

    with pytest.raises(HTTPException) as error:
        await resolve_project_access(scope)

    assert error.value.status_code == 403