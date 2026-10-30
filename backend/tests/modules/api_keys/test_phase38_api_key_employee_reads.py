from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException, Response

from app.modules.api_keys import employee_read_router as module
from app.modules.api_keys.authentication import APIKeyPrincipal


def make_principal():
    return APIKeyPrincipal(
        key_id=uuid4(),
        workspace_id=uuid4(),
        user_id=uuid4(),
        membership_id=uuid4(),
        scopes=frozenset({"employees.read"}),
    )


@pytest.mark.asyncio
async def test_workspace_mismatch_prevents_tenant_access(monkeypatch):
    principal = make_principal()
    calls = []

    @asynccontextmanager
    async def tenant_session(*args, **kwargs):
        calls.append(kwargs)
        yield None

    monkeypatch.setattr(
        module,
        "authorized_tenant_session",
        tenant_session,
    )

    dependency = module.get_employee_key_scope(
        workspace_id=uuid4(),
        principal=principal,
        control_session=object(),
    )

    with pytest.raises(HTTPException) as error:
        await anext(dependency)

    assert error.value.status_code == 401
    assert calls == []


@pytest.mark.asyncio
async def test_missing_scope_prevents_tenant_access():
    principal = make_principal()

    principal = APIKeyPrincipal(
        key_id=principal.key_id,
        workspace_id=principal.workspace_id,
        user_id=principal.user_id,
        membership_id=principal.membership_id,
        scopes=frozenset({"reports.self.read"}),
    )

    dependency = module.get_employee_key_scope(
        workspace_id=principal.workspace_id,
        principal=principal,
        control_session=object(),
    )

    with pytest.raises(HTTPException) as error:
        await anext(dependency)

    assert error.value.status_code == 403


@pytest.mark.asyncio
async def test_verified_scope_uses_creator_and_tenant_session(
    monkeypatch,
):
    principal = make_principal()
    session = object()
    control = object()
    calls = []

    context = SimpleNamespace(
        workspace_id=principal.workspace_id,
        user_id=principal.user_id,
        membership_id=principal.membership_id,
        role_key="owner",
        schema_version=None,
    )

    @asynccontextmanager
    async def tenant_session(control_session, **kwargs):
        calls.append((control_session, kwargs))
        yield context, session

    class Permissions:
        def __init__(self, scope):
            assert scope is context

        def require(self, permission):
            assert permission == "employees.read"

    monkeypatch.setattr(
        module,
        "authorized_tenant_session",
        tenant_session,
    )
    monkeypatch.setattr(
        module,
        "WorkspacePermissionService",
        Permissions,
    )

    dependency = module.get_employee_key_scope(
        workspace_id=principal.workspace_id,
        principal=principal,
        control_session=control,
    )

    scope = await anext(dependency)

    try:
        assert scope.session is session
        assert scope.context is context

        assert calls == [
            (
                control,
                {
                    "workspace_id": principal.workspace_id,
                    "user_id": principal.user_id,
                },
            )
        ]
    finally:
        await dependency.aclose()


@pytest.mark.asyncio
async def test_replaced_membership_is_rejected(monkeypatch):
    principal = make_principal()

    context = SimpleNamespace(
        membership_id=uuid4(),
        role_key="owner",
    )

    @asynccontextmanager
    async def tenant_session(*args, **kwargs):
        yield context, object()

    monkeypatch.setattr(
        module,
        "authorized_tenant_session",
        tenant_session,
    )

    dependency = module.get_employee_key_scope(
        workspace_id=principal.workspace_id,
        principal=principal,
        control_session=object(),
    )

    with pytest.raises(HTTPException) as error:
        await anext(dependency)

    assert error.value.status_code == 401


@pytest.mark.asyncio
async def test_removed_permission_is_rejected(monkeypatch):
    principal = make_principal()

    context = SimpleNamespace(
        membership_id=principal.membership_id,
        role_key="member",
    )

    @asynccontextmanager
    async def tenant_session(*args, **kwargs):
        yield context, object()

    class Permissions:
        def __init__(self, scope):
            pass

        def require(self, permission):
            raise HTTPException(
                status_code=403,
                detail="Permission removed.",
            )

    monkeypatch.setattr(
        module,
        "authorized_tenant_session",
        tenant_session,
    )
    monkeypatch.setattr(
        module,
        "WorkspacePermissionService",
        Permissions,
    )

    dependency = module.get_employee_key_scope(
        workspace_id=principal.workspace_id,
        principal=principal,
        control_session=object(),
    )

    with pytest.raises(HTTPException) as error:
        await anext(dependency)

    assert error.value.status_code == 403


@pytest.mark.asyncio
async def test_list_reuses_employee_service_and_filters(monkeypatch):
    session = object()
    scope = SimpleNamespace(session=session)
    department_id = uuid4()
    expected = object()
    read = AsyncMock(return_value=expected)

    class Service:
        def __init__(self, supplied_session):
            assert supplied_session is session

        list_employees = read

    monkeypatch.setattr(module, "EmployeeService", Service)

    response = Response()

    result = await module.list_integration_employees(
        scope=scope,
        response=response,
        department_id=department_id,
        team_id=None,
        manager_id=None,
        employment_status="active",
        include_inactive=False,
        search="Alex",
    )

    assert result is expected
    assert response.headers["cache-control"] == "no-store"

    read.assert_awaited_once_with(
        department_id=department_id,
        team_id=None,
        manager_id=None,
        employment_status="active",
        include_inactive=False,
        search="Alex",
    )


@pytest.mark.asyncio
async def test_detail_reuses_employee_service(monkeypatch):
    session = object()
    scope = SimpleNamespace(session=session)
    employee_id = uuid4()
    expected = object()
    read = AsyncMock(return_value=expected)

    class Service:
        def __init__(self, supplied_session):
            assert supplied_session is session

        get_employee = read

    monkeypatch.setattr(module, "EmployeeService", Service)

    result = await module.get_integration_employee(
        employee_id=employee_id,
        scope=scope,
        response=Response(),
    )

    assert result is expected
    read.assert_awaited_once_with(employee_id=employee_id)


@pytest.mark.parametrize(
    "suffix",
    ["/employees", "/employees/{employee_id}"],
)
def test_employee_integration_registered_with_api_key_security(
    suffix,
):
    from app.main import app

    path = (
        "/api/v1/workspaces/{workspace_id}/integrations"
        + suffix
    )

    operation = app.openapi()["paths"][path]["get"]

    assert {"WorkspaceAPIKey": []} in operation["security"]