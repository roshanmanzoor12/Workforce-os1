from __future__ import annotations

import importlib
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.modules.employees.scope_access import (
    can_access_employee_row,
    require_employee_action,
    require_employee_workspace_scope,
)
from app.modules.workspace_permissions.access_context import (
    WorkspaceAccessContext,
)
from app.modules.workspace_permissions.saved_scopes import (
    merge_saved_scopes,
)


module = importlib.import_module(
    "app.modules.workspace_permissions.request_scopes"
)


def make_context(
    permissions: frozenset[str] = frozenset({"employees.read"}),
) -> WorkspaceAccessContext:
    return WorkspaceAccessContext(
        workspace_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        membership_id=uuid.uuid4(),
        employee_id=None,
        role_key="member",
        permissions=permissions,
        scopes=(),
    )


@pytest.mark.asyncio
async def test_authorized_control_session_reaches_resolver(monkeypatch):
    context = make_context()
    control = object()
    scope = SimpleNamespace(control_session=control)
    expected = object()
    resolver = AsyncMock(return_value=expected)

    monkeypatch.setattr(module, "resolve_saved_scope_access", resolver)

    assert (
        await module.resolve_request_saved_scopes(scope, context)
        is expected
    )
    resolver.assert_awaited_once_with(
        control,
        tenant_scope=scope,
        context=context,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("include_field", [False, True])
async def test_legacy_scope_receives_no_additional_grants(
    include_field,
    monkeypatch,
):
    context = make_context()
    scope = SimpleNamespace()

    if include_field:
        scope.control_session = None

    resolver = AsyncMock()
    monkeypatch.setattr(module, "resolve_saved_scope_access", resolver)

    assert (
        await module.resolve_request_saved_scopes(scope, context)
        is context
    )
    resolver.assert_not_awaited()


@pytest.mark.asyncio
async def test_saved_scope_denial_is_not_silently_ignored(monkeypatch):
    scope = SimpleNamespace(control_session=object())
    resolver = AsyncMock(
        side_effect=HTTPException(
            status_code=403,
            detail="Membership is unavailable.",
        )
    )
    monkeypatch.setattr(module, "resolve_saved_scope_access", resolver)

    with pytest.raises(HTTPException) as error:
        await module.resolve_request_saved_scopes(
            scope,
            make_context(),
        )

    assert error.value.status_code == 403


@pytest.mark.parametrize("scope_type", ["team", "department"])
def test_grant_expands_only_matching_employee_resources(scope_type):
    context = make_context()
    resource_id = uuid.uuid4()

    expanded = merge_saved_scopes(
        context,
        (
            SimpleNamespace(
                membership_id=context.membership_id,
                scope_type=scope_type,
                resource_id=resource_id,
            ),
        ),
    )

    matching = SimpleNamespace(
        id=uuid.uuid4(),
        team_id=resource_id if scope_type == "team" else None,
        department_id=(
            resource_id if scope_type == "department" else None
        ),
    )
    unrelated = SimpleNamespace(
        id=uuid.uuid4(),
        team_id=uuid.uuid4(),
        department_id=uuid.uuid4(),
    )

    assert can_access_employee_row(expanded, matching)
    assert not can_access_employee_row(expanded, unrelated)
    assert expanded.permissions == context.permissions
    assert not expanded.is_workspace_scoped

    with pytest.raises(HTTPException):
        require_employee_action(expanded, "update")


def test_management_permission_and_team_grant_do_not_allow_workspace_mutation():
    context = make_context(
        frozenset({"employees.read", "employees.manage"})
    )
    expanded = merge_saved_scopes(
        context,
        (
            SimpleNamespace(
                membership_id=context.membership_id,
                scope_type="team",
                resource_id=uuid.uuid4(),
            ),
        ),
    )

    require_employee_action(expanded, "create")

    with pytest.raises(HTTPException):
        require_employee_workspace_scope(expanded)