from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.employees import access_service as access_module
from app.modules.employees import router as routes
from app.modules.employees.scope_access import build_employee_access
from app.modules.employees.scoped_service import ScopedEmployeeService


def make_scope():
    return SimpleNamespace(
        workspace_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        membership_id=uuid.uuid4(),
        role_key="member",
        effective_permissions=frozenset({"employees.all.read"}),
        session=object(),
    )


@pytest.mark.asyncio
async def test_http_factory_builds_scoped_service(monkeypatch):
    scope = make_scope()
    context = build_employee_access(scope, None)
    resolver = AsyncMock(return_value=context)

    monkeypatch.setattr(
        routes,
        "resolve_employee_access",
        resolver,
    )

    service = await routes.get_scoped_employee_service(scope)

    assert isinstance(service, ScopedEmployeeService)
    assert service.context is context
    assert service.session is scope.session

    resolver.assert_awaited_once_with(scope)


@pytest.mark.asyncio
async def test_detail_route_uses_scoped_factory(monkeypatch):
    scope = make_scope()
    employee_id = uuid.uuid4()
    expected = object()

    service = SimpleNamespace(
        get_employee=AsyncMock(return_value=expected)
    )

    factory = AsyncMock(return_value=service)

    monkeypatch.setattr(
        routes,
        "get_scoped_employee_service",
        factory,
    )

    assert await routes.get_employee(
        employee_id,
        scope,
    ) is expected

    service.get_employee.assert_awaited_once_with(
        employee_id=employee_id
    )


@pytest.mark.asyncio
async def test_list_route_forwards_filters_to_scoped_service(
    monkeypatch,
):
    scope = make_scope()
    team_id = uuid.uuid4()
    expected = object()

    service = SimpleNamespace(
        list_employees=AsyncMock(return_value=expected)
    )

    monkeypatch.setattr(
        routes,
        "get_scoped_employee_service",
        AsyncMock(return_value=service),
    )

    result = await routes.list_employees(
        scope=scope,
        department_id=None,
        team_id=team_id,
        manager_id=None,
        employment_status=None,
        include_inactive=False,
        search="test",
    )

    assert result is expected

    service.list_employees.assert_awaited_once_with(
        department_id=None,
        team_id=team_id,
        manager_id=None,
        employment_status=None,
        include_inactive=False,
        search="test",
    )


@pytest.mark.asyncio
async def test_application_api_resolves_effective_snapshot(
    monkeypatch,
):
    workspace_id = uuid.uuid4()
    user_id = uuid.uuid4()
    membership_id = uuid.uuid4()

    wrapper = access_module.EmployeeAccessService(
        workspace_id=workspace_id,
        actor_user_id=user_id,
        control_session=object(),
        tenant_session=object(),
    )

    membership = SimpleNamespace(
        id=membership_id,
        role_key="custom-reader",
    )

    wrapper.access = SimpleNamespace(
        require_active_member=AsyncMock(return_value=membership)
    )

    permissions = frozenset({"employees.self.read"})
    resolve_permissions = AsyncMock(return_value=permissions)

    monkeypatch.setattr(
        access_module,
        "resolve_membership_permissions",
        resolve_permissions,
    )

    context = object()
    resolve_context = AsyncMock(return_value=context)

    monkeypatch.setattr(
        access_module,
        "resolve_employee_access",
        resolve_context,
    )

    expected = object()
    constructor = MagicMock(return_value=expected)

    monkeypatch.setattr(
        access_module,
        "ScopedEmployeeService",
        constructor,
    )

    assert await wrapper._scoped_employee_service() is expected

    scope = resolve_context.await_args.args[0]

    assert scope.workspace_id == workspace_id
    assert scope.user_id == user_id
    assert scope.membership_id == membership_id
    assert scope.effective_permissions == permissions
    assert scope.session is wrapper.tenant_session

    resolve_permissions.assert_awaited_once_with(
        wrapper.control_session,
        workspace_id=workspace_id,
        membership=membership,
    )


@pytest.mark.asyncio
async def test_application_api_employee_read_uses_scoped_service(
    monkeypatch,
):
    wrapper = access_module.EmployeeAccessService(
        workspace_id=uuid.uuid4(),
        actor_user_id=uuid.uuid4(),
        control_session=object(),
        tenant_session=object(),
    )

    employee_id = uuid.uuid4()
    expected = object()

    service = SimpleNamespace(
        get_employee=AsyncMock(return_value=expected)
    )

    monkeypatch.setattr(
        wrapper,
        "_scoped_employee_service",
        AsyncMock(return_value=service),
    )

    assert await wrapper.get_employee(
        employee_id=employee_id
    ) is expected

    service.get_employee.assert_awaited_once_with(
        employee_id=employee_id
    )