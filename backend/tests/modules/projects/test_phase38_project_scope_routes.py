import importlib
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.modules.projects.schemas import ProjectCreate, ProjectUpdate
from app.modules.workspace_permissions.access_context import (
    WorkspaceAccessContext,
)
from app.modules.workspace_permissions.scopes import self_scope


routes = importlib.import_module("app.modules.projects.router")


def make_scope(permissions=None):
    return SimpleNamespace(
        workspace_id=uuid4(),
        user_id=uuid4(),
        membership_id=uuid4(),
        role_key="member",
        effective_permissions=(
            frozenset({"projects.view", "projects.manage"})
            if permissions is None
            else permissions
        ),
        session=SimpleNamespace(
            commit=AsyncMock(),
            rollback=AsyncMock(),
        ),
    )


def context_for(scope):
    return WorkspaceAccessContext(
        workspace_id=scope.workspace_id,
        user_id=scope.user_id,
        membership_id=scope.membership_id,
        employee_id=uuid4(),
        role_key=scope.role_key,
        permissions=scope.effective_permissions,
        scopes=(self_scope(),),
    )


@pytest.mark.asyncio
async def test_factory_rejects_permission_before_identity_query(
    monkeypatch,
):
    resolver = AsyncMock()
    monkeypatch.setattr(routes, "resolve_project_access", resolver)

    with pytest.raises(HTTPException) as error:
        await routes.get_project_service(
            make_scope(permissions=frozenset())
        )

    assert error.value.status_code == 403
    resolver.assert_not_awaited()


@pytest.mark.asyncio
async def test_factory_rejects_foreign_workspace_context(monkeypatch):
    scope = make_scope()
    other = make_scope()
    resolver = AsyncMock(return_value=context_for(other))
    monkeypatch.setattr(routes, "resolve_project_access", resolver)

    with pytest.raises(HTTPException) as error:
        await routes.get_project_service(scope)

    assert error.value.status_code == 403


@pytest.mark.asyncio
async def test_factory_uses_scoped_service(monkeypatch):
    scope = make_scope()
    context = context_for(scope)

    monkeypatch.setattr(
        routes,
        "resolve_project_access",
        AsyncMock(return_value=context),
    )

    service = await routes.get_project_service(scope)

    assert service.context is context
    assert service.session is scope.session


@pytest.mark.asyncio
async def test_list_route_uses_scoped_service(monkeypatch):
    scope = make_scope()
    service = SimpleNamespace(
        list=AsyncMock(return_value=([], 0))
    )
    factory = AsyncMock(return_value=service)
    monkeypatch.setattr(routes, "get_project_service", factory)

    result = await routes.list_projects(
        scope,
        offset=10,
        limit=5,
        status=None,
    )

    assert result.total == 0
    factory.assert_awaited_once_with(scope)
    service.list.assert_awaited_once_with(
        offset=10,
        limit=5,
        status=None,
    )


@pytest.mark.asyncio
async def test_failed_create_rolls_back(monkeypatch):
    scope = make_scope()
    service = SimpleNamespace(
        create=AsyncMock(
            side_effect=HTTPException(status_code=403, detail="Denied")
        )
    )
    monkeypatch.setattr(
        routes,
        "get_project_service",
        AsyncMock(return_value=service),
    )

    with pytest.raises(HTTPException):
        await routes.create_project(
            ProjectCreate(name="Website"),
            scope,
        )

    scope.session.commit.assert_not_awaited()
    scope.session.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_failed_update_rolls_back(monkeypatch):
    scope = make_scope()
    service = SimpleNamespace(
        update=AsyncMock(
            side_effect=HTTPException(status_code=404, detail="Not found")
        )
    )
    monkeypatch.setattr(
        routes,
        "get_project_service",
        AsyncMock(return_value=service),
    )

    with pytest.raises(HTTPException):
        await routes.update_project(
            uuid4(),
            ProjectUpdate(name="Changed"),
            scope,
        )

    scope.session.commit.assert_not_awaited()
    scope.session.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_failed_delete_rolls_back(monkeypatch):
    scope = make_scope()
    service = SimpleNamespace(
        delete=AsyncMock(
            side_effect=HTTPException(status_code=404, detail="Not found")
        )
    )
    monkeypatch.setattr(
        routes,
        "get_project_service",
        AsyncMock(return_value=service),
    )

    with pytest.raises(HTTPException):
        await routes.delete_project(uuid4(), scope)

    scope.session.commit.assert_not_awaited()
    scope.session.rollback.assert_awaited_once()


def test_project_operations_remain_in_real_app_openapi():
    from app.main import app

    paths = app.openapi()["paths"]
    base = "/api/v1/workspaces/{workspace_id}/projects"

    assert "get" in paths[base]
    assert "post" in paths[base]
    assert "get" in paths[base + "/{project_id}"]
    assert "patch" in paths[base + "/{project_id}"]
    assert "delete" in paths[base + "/{project_id}"]