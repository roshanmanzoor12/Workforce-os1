from __future__ import annotations

import importlib
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.modules.workspace_permissions.access_context import (
    WorkspaceAccessContext,
)
from app.modules.workspace_permissions.saved_scopes import (
    merge_saved_scopes,
)


routes = importlib.import_module("app.modules.projects.router")


def make_scope():
    return SimpleNamespace(
        workspace_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        membership_id=uuid.uuid4(),
        role_key="member",
        effective_permissions=frozenset({"projects.view"}),
        session=object(),
        control_session=object(),
    )


def make_context(scope):
    return WorkspaceAccessContext(
        workspace_id=scope.workspace_id,
        user_id=scope.user_id,
        membership_id=scope.membership_id,
        employee_id=None,
        role_key=scope.role_key,
        permissions=scope.effective_permissions,
        scopes=(),
    )


@pytest.mark.asyncio
async def test_project_factory_passes_saved_scope_context_to_service(
    monkeypatch,
):
    scope = make_scope()
    base = make_context(scope)
    expanded = merge_saved_scopes(
        base,
        (
            SimpleNamespace(
                membership_id=base.membership_id,
                scope_type="team",
                resource_id=uuid.uuid4(),
            ),
        ),
    )

    monkeypatch.setattr(
        routes,
        "resolve_project_access",
        AsyncMock(return_value=base),
    )
    loader = AsyncMock(return_value=expanded)
    monkeypatch.setattr(
        routes,
        "resolve_request_saved_scopes",
        loader,
    )

    expected = object()
    constructor = MagicMock(return_value=expected)
    monkeypatch.setattr(
        routes,
        "ScopedProjectService",
        constructor,
    )

    assert await routes.get_project_service(scope) is expected
    loader.assert_awaited_once_with(scope, base)
    constructor.assert_called_once_with(scope.session, expanded)
    assert expanded.permissions == base.permissions
    assert not expanded.is_workspace_scoped


@pytest.mark.asyncio
async def test_missing_project_permission_stops_all_context_resolution(
    monkeypatch,
):
    scope = make_scope()
    scope.effective_permissions = frozenset()

    resolver = AsyncMock()
    loader = AsyncMock()
    constructor = MagicMock()

    monkeypatch.setattr(routes, "resolve_project_access", resolver)
    monkeypatch.setattr(routes, "resolve_request_saved_scopes", loader)
    monkeypatch.setattr(routes, "ScopedProjectService", constructor)

    with pytest.raises(HTTPException) as error:
        await routes.get_project_service(scope)

    assert error.value.status_code == 403
    resolver.assert_not_awaited()
    loader.assert_not_awaited()
    constructor.assert_not_called()


@pytest.mark.asyncio
async def test_scope_resolution_denial_stops_service_construction(
    monkeypatch,
):
    scope = make_scope()

    monkeypatch.setattr(
        routes,
        "resolve_project_access",
        AsyncMock(return_value=make_context(scope)),
    )
    monkeypatch.setattr(
        routes,
        "resolve_request_saved_scopes",
        AsyncMock(
            side_effect=HTTPException(
                status_code=403,
                detail="Access context must be refreshed.",
            )
        ),
    )
    constructor = MagicMock()
    monkeypatch.setattr(routes, "ScopedProjectService", constructor)

    with pytest.raises(HTTPException) as error:
        await routes.get_project_service(scope)

    assert error.value.status_code == 403
    constructor.assert_not_called()