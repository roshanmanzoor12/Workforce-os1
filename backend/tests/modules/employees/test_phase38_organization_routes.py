from __future__ import annotations

import importlib
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.employees.organization_service import (
    ScopedOrganizationService,
)
from app.modules.employees.schemas import (
    DepartmentCreateRequest,
    DepartmentUpdateRequest,
    TeamCreateRequest,
    TeamUpdateRequest,
)


routes = importlib.import_module("app.modules.employees.router")
access_module = importlib.import_module(
    "app.modules.employees.access_service",
)


@pytest.mark.asyncio
async def test_http_factory_builds_scoped_organization_service(
    monkeypatch,
):
    context = object()
    scope = SimpleNamespace(session=object())
    resolver = AsyncMock(return_value=context)

    monkeypatch.setattr(
        routes,
        "resolve_employee_access",
        resolver,
    )

    service = await routes.get_scoped_organization_service(scope)

    assert isinstance(service, ScopedOrganizationService)
    assert service.context is context
    assert service.session is scope.session
    resolver.assert_awaited_once_with(scope)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method",
    [
        "create_department",
        "list_departments",
        "get_department",
        "update_department",
        "delete_department",
        "create_team",
        "list_teams",
        "get_team",
        "update_team",
        "delete_team",
    ],
)
async def test_every_organization_route_uses_scoped_factory(
    method,
    monkeypatch,
):
    scope = object()
    expected = object()
    operation = AsyncMock(return_value=expected)
    service = SimpleNamespace(**{method: operation})
    factory = AsyncMock(return_value=service)

    monkeypatch.setattr(
        routes,
        "get_scoped_organization_service",
        factory,
    )

    # Any accidental fallback to the old factory fails immediately.
    monkeypatch.setattr(
        routes,
        "get_employee_service",
        MagicMock(side_effect=AssertionError("Unscoped factory used")),
    )

    target_id = uuid.uuid4()

    if method == "create_department":
        payload = DepartmentCreateRequest(name="Engineering")
        result = await routes.create_department(payload, scope)
        operation.assert_awaited_once_with(payload)

    elif method == "list_departments":
        result = await routes.list_departments(
            scope,
            include_inactive=True,
        )
        operation.assert_awaited_once_with(include_inactive=True)

    elif method == "get_department":
        result = await routes.get_department(target_id, scope)
        operation.assert_awaited_once_with(
            department_id=target_id,
        )

    elif method == "update_department":
        payload = DepartmentUpdateRequest(description="Updated")
        result = await routes.update_department(
            target_id,
            payload,
            scope,
        )
        operation.assert_awaited_once_with(
            payload,
            department_id=target_id,
        )

    elif method == "delete_department":
        result = await routes.delete_department(target_id, scope)
        operation.assert_awaited_once_with(
            department_id=target_id,
        )

    elif method == "create_team":
        payload = TeamCreateRequest(name="Platform")
        result = await routes.create_team(payload, scope)
        operation.assert_awaited_once_with(payload)

    elif method == "list_teams":
        result = await routes.list_teams(
            scope,
            department_id=target_id,
            include_inactive=True,
        )
        operation.assert_awaited_once_with(
            department_id=target_id,
            include_inactive=True,
        )

    elif method == "get_team":
        result = await routes.get_team(target_id, scope)
        operation.assert_awaited_once_with(team_id=target_id)

    elif method == "update_team":
        payload = TeamUpdateRequest(description="Updated")
        result = await routes.update_team(
            target_id,
            payload,
            scope,
        )
        operation.assert_awaited_once_with(
            payload,
            team_id=target_id,
        )

    else:
        result = await routes.delete_team(target_id, scope)
        operation.assert_awaited_once_with(team_id=target_id)

    assert result is expected
    factory.assert_awaited_once_with(scope)


@pytest.mark.asyncio
async def test_application_factory_resolves_effective_permissions(
    monkeypatch,
):
    control_session = object()
    tenant_session = object()
    workspace_id = uuid.uuid4()
    user_id = uuid.uuid4()

    membership = SimpleNamespace(
        id=uuid.uuid4(),
        role_key="member",
    )

    permissions = frozenset({"departments.read", "teams.read"})
    context = object()
    expected = object()

    wrapper = access_module.EmployeeAccessService(
        workspace_id=workspace_id,
        actor_user_id=user_id,
        control_session=control_session,
        tenant_session=tenant_session,
    )

    wrapper.access.require_active_member = AsyncMock(
        return_value=membership,
    )

    permission_resolver = AsyncMock(return_value=permissions)
    context_resolver = AsyncMock(return_value=context)
    constructor = MagicMock(return_value=expected)

    monkeypatch.setattr(
        access_module,
        "resolve_membership_permissions",
        permission_resolver,
    )
    monkeypatch.setattr(
        access_module,
        "resolve_employee_access",
        context_resolver,
    )
    monkeypatch.setattr(
        access_module,
        "ScopedOrganizationService",
        constructor,
    )

    assert await wrapper._scoped_organization_service() is expected

    wrapper.access.require_active_member.assert_awaited_once_with(
        workspace_id=workspace_id,
        user_id=user_id,
    )

    permission_resolver.assert_awaited_once_with(
        control_session,
        workspace_id=workspace_id,
        membership=membership,
    )

    scope = context_resolver.await_args.args[0]

    assert scope.workspace_id == workspace_id
    assert scope.user_id == user_id
    assert scope.membership_id == membership.id
    assert scope.role_key == membership.role_key
    assert scope.effective_permissions == permissions
    assert scope.session is tenant_session

    constructor.assert_called_once_with(
        tenant_session,
        context,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "resource",
    ["department", "team"],
)
async def test_application_detail_uses_scoped_service(resource):
    wrapper = access_module.EmployeeAccessService(
        workspace_id=uuid.uuid4(),
        actor_user_id=uuid.uuid4(),
        control_session=object(),
        tenant_session=object(),
    )

    method = f"get_{resource}"
    expected = object()
    operation = AsyncMock(return_value=expected)

    wrapper._scoped_organization_service = AsyncMock(
        return_value=SimpleNamespace(**{method: operation}),
    )

    target_id = uuid.uuid4()
    arguments = {f"{resource}_id": target_id}

    assert await getattr(wrapper, method)(**arguments) is expected
    operation.assert_awaited_once_with(**arguments)


@pytest.mark.asyncio
async def test_application_membership_denial_stops_tenant_resolution(
    monkeypatch,
):
    from fastapi import HTTPException

    wrapper = access_module.EmployeeAccessService(
        workspace_id=uuid.uuid4(),
        actor_user_id=uuid.uuid4(),
        control_session=object(),
        tenant_session=object(),
    )

    wrapper.access.require_active_member = AsyncMock(
        side_effect=HTTPException(
            status_code=403,
            detail="Membership required.",
        ),
    )

    permission_resolver = AsyncMock()
    context_resolver = AsyncMock()

    monkeypatch.setattr(
        access_module,
        "resolve_membership_permissions",
        permission_resolver,
    )
    monkeypatch.setattr(
        access_module,
        "resolve_employee_access",
        context_resolver,
    )

    with pytest.raises(HTTPException) as error:
        await wrapper._scoped_organization_service()

    assert error.value.status_code == 403
    permission_resolver.assert_not_awaited()
    context_resolver.assert_not_awaited()