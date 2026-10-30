from __future__ import annotations

import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy.dialects import postgresql

from app.modules.employees.organization_policy import (
    department_scope_predicate,
    require_organization_permission,
    team_scope_predicate,
)
from app.modules.workspace_permissions.access_context import (
    WorkspaceAccessContext,
)
from app.modules.workspace_permissions.scopes import (
    WorkspaceResourceScope,
    WorkspaceScopeType,
)


def make_context(
    *,
    permissions=(),
    workspace=False,
    department_ids=(),
    team_ids=(),
    scopes=(),
    role_key="member",
):
    grants = tuple(scopes)

    if workspace:
        grants += (
            WorkspaceResourceScope(
                type=WorkspaceScopeType.WORKSPACE,
            ),
        )

    return WorkspaceAccessContext(
        user_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        membership_id=uuid.uuid4(),
        employee_id=uuid.uuid4(),
        role_key=role_key,
        permissions=frozenset(permissions),
        scopes=grants,
        department_ids=frozenset(department_ids),
        team_ids=frozenset(team_ids),
    )


def compile_predicate(predicate):
    return predicate.compile(
        dialect=postgresql.dialect(),
        compile_kwargs={"render_postcompile": True},
    )


@pytest.mark.parametrize("resource", ["departments", "teams"])
@pytest.mark.parametrize("suffix", ["read", "view"])
def test_read_permission_is_accepted(resource, suffix):
    context = make_context(
        permissions={f"{resource}.{suffix}"},
    )

    require_organization_permission(
        context,
        resource=resource,
    )


@pytest.mark.parametrize("resource", ["departments", "teams"])
def test_empty_owner_snapshot_does_not_grant_access(resource):
    context = make_context(
        role_key="owner",
        workspace=True,
    )

    with pytest.raises(HTTPException) as error:
        require_organization_permission(
            context,
            resource=resource,
        )

    assert error.value.status_code == 403


@pytest.mark.parametrize("resource", ["departments", "teams"])
def test_manage_permission_does_not_expand_scope(resource):
    context = make_context(
        permissions={f"{resource}.manage"},
    )

    with pytest.raises(HTTPException) as error:
        require_organization_permission(
            context,
            resource=resource,
            manage=True,
        )

    assert error.value.status_code == 403
    assert not context.is_workspace_scoped


@pytest.mark.parametrize("resource", ["departments", "teams"])
def test_workspace_scope_alone_does_not_grant_management(resource):
    context = make_context(workspace=True)

    with pytest.raises(HTTPException) as error:
        require_organization_permission(
            context,
            resource=resource,
            manage=True,
        )

    assert error.value.status_code == 403


@pytest.mark.parametrize("resource", ["departments", "teams"])
def test_manage_and_workspace_scope_allow_mutations(resource):
    context = make_context(
        permissions={f"{resource}.manage"},
        workspace=True,
    )

    require_organization_permission(
        context,
        resource=resource,
        manage=True,
    )


@pytest.mark.parametrize("resource", ["departments", "teams"])
def test_manage_is_not_implicitly_a_read_permission(resource):
    context = make_context(
        permissions={f"{resource}.manage"},
        workspace=True,
    )

    with pytest.raises(HTTPException):
        require_organization_permission(
            context,
            resource=resource,
        )


def test_unknown_resource_is_rejected():
    with pytest.raises(ValueError):
        require_organization_permission(
            make_context(),
            resource="unknown",
        )


def test_empty_scope_has_no_department_visibility():
    compiled = compile_predicate(
        department_scope_predicate(make_context()),
    )

    assert str(compiled) == "false"


def test_empty_scope_has_no_team_visibility():
    compiled = compile_predicate(
        team_scope_predicate(make_context()),
    )

    assert str(compiled) == "false"


def test_own_department_does_not_grant_all_its_teams():
    department_id = uuid.uuid4()

    context = make_context(
        department_ids={department_id},
    )

    compiled = compile_predicate(team_scope_predicate(context))

    assert str(compiled) == "false"


def test_explicit_department_scope_authorizes_its_teams():
    department_id = uuid.uuid4()

    context = make_context(
        scopes=(
            WorkspaceResourceScope(
                type=WorkspaceScopeType.DEPARTMENT,
                id=department_id,
            ),
        ),
    )

    compiled = compile_predicate(team_scope_predicate(context))

    assert department_id in compiled.params.values()


def test_team_visibility_contains_only_authorized_team_id():
    team_id = uuid.uuid4()

    context = make_context(team_ids={team_id})

    compiled = compile_predicate(team_scope_predicate(context))

    assert team_id in compiled.params.values()


def test_team_scope_can_resolve_its_parent_department():
    team_id = uuid.uuid4()

    context = make_context(
        scopes=(
            WorkspaceResourceScope(
                type=WorkspaceScopeType.TEAM,
                id=team_id,
            ),
        ),
    )

    compiled = compile_predicate(
        department_scope_predicate(context),
    )

    assert team_id in compiled.params.values()
    assert "SELECT" in str(compiled)


@pytest.mark.parametrize(
    "predicate",
    [department_scope_predicate, team_scope_predicate],
)
def test_workspace_scope_has_no_record_filter(predicate):
    context = make_context(workspace=True)

    assert str(compile_predicate(predicate(context))) == "true"