from __future__ import annotations

import importlib
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.core.exceptions import ResourceNotFound
from app.modules.workspace_rbac.scope_schemas import (
    ScopeGrantCreateRequest,
)


services = importlib.import_module(
    "app.modules.workspace_rbac.scope_service",
)


def setup_service(monkeypatch, *, role_key="owner"):
    workspace_id = uuid.uuid4()
    actor_user_id = uuid.uuid4()
    actor_membership_id = uuid.uuid4()
    target_id = uuid.uuid4()

    control = SimpleNamespace(
        commit=AsyncMock(),
        rollback=AsyncMock(),
    )

    scope = SimpleNamespace(
        workspace_id=workspace_id,
        user_id=actor_user_id,
        membership_id=actor_membership_id,
        session=SimpleNamespace(scalar=AsyncMock()),
    )

    actor = SimpleNamespace(
        id=actor_membership_id,
        workspace_id=workspace_id,
        user_id=actor_user_id,
        status="active",
        role_key=role_key,
    )

    target = SimpleNamespace(
        id=target_id,
        workspace_id=workspace_id,
        user_id=uuid.uuid4(),
        status="active",
        role_key="member",
    )

    repository = SimpleNamespace(
        require_workspace=AsyncMock(),
        require_membership=AsyncMock(side_effect=[actor, target]),
        list_for=AsyncMock(return_value=()),
        add=AsyncMock(),
        remove=AsyncMock(return_value=True),
    )

    resources = SimpleNamespace(
        require_active=AsyncMock(),
    )

    permissions = AsyncMock(return_value=frozenset({"roles.manage"}))

    monkeypatch.setattr(
        services,
        "resolve_membership_permissions",
        permissions,
    )

    service = services.MembershipScopeGrantService(control, scope)
    service.repository = repository
    service.resources = resources

    return SimpleNamespace(
        service=service,
        control=control,
        scope=scope,
        actor=actor,
        target=target,
        repository=repository,
        resources=resources,
        permissions=permissions,
    )


@pytest.mark.asyncio
async def test_grant_uses_authenticated_actor_as_grantor(monkeypatch):
    setup = setup_service(monkeypatch)
    resource_id = uuid.uuid4()

    setup.repository.add.return_value = SimpleNamespace(
        membership_id=setup.target.id,
        scope_type="team",
        resource_id=resource_id,
        granted_by_user_id=setup.actor.user_id,
        created_at=datetime.now(timezone.utc),
    )

    response = await setup.service.grant(
        ScopeGrantCreateRequest(
            scope_type="team",
            resource_id=resource_id,
        ),
        membership_id=setup.target.id,
    )

    assert response.granted_by_user_id == setup.actor.user_id

    setup.repository.require_workspace.assert_awaited_once_with(
        workspace_id=setup.scope.workspace_id,
        lock=True,
    )

    setup.resources.require_active.assert_awaited_once_with(
        scope_type="team",
        resource_id=resource_id,
    )

    assert (
        setup.repository.add.await_args.kwargs["granted_by_user_id"]
        == setup.actor.user_id
    )

    assert setup.permissions.await_count == 2
    setup.control.commit.assert_awaited_once()
    setup.control.rollback.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("role_key", ["admin", "manager", "member"])
async def test_non_owner_cannot_grant_even_with_roles_manage(
    monkeypatch,
    role_key,
):
    setup = setup_service(monkeypatch, role_key=role_key)

    with pytest.raises(HTTPException) as error:
        await setup.service.grant(
            ScopeGrantCreateRequest(
                scope_type="team",
                resource_id=uuid.uuid4(),
            ),
            membership_id=setup.target.id,
        )

    assert error.value.status_code == 403
    setup.resources.require_active.assert_not_awaited()
    setup.repository.add.assert_not_awaited()
    setup.control.commit.assert_not_awaited()
    setup.control.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_empty_owner_permissions_cannot_grant(monkeypatch):
    setup = setup_service(monkeypatch)
    setup.permissions.return_value = frozenset()

    with pytest.raises(HTTPException):
        await setup.service.grant(
            ScopeGrantCreateRequest(
                scope_type="department",
                resource_id=uuid.uuid4(),
            ),
            membership_id=setup.target.id,
        )

    setup.repository.add.assert_not_awaited()
    setup.control.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_missing_tenant_resource_stops_insert(monkeypatch):
    setup = setup_service(monkeypatch)

    setup.resources.require_active.side_effect = ResourceNotFound(
        "Resource was not found.",
    )

    with pytest.raises(ResourceNotFound):
        await setup.service.grant(
            ScopeGrantCreateRequest(
                scope_type="department",
                resource_id=uuid.uuid4(),
            ),
            membership_id=setup.target.id,
        )

    setup.repository.add.assert_not_awaited()
    setup.control.commit.assert_not_awaited()
    setup.control.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_banned_target_stops_resource_resolution(monkeypatch):
    setup = setup_service(monkeypatch)

    setup.permissions.side_effect = [
        frozenset({"roles.manage"}),
        HTTPException(status_code=403, detail="Workspace access is banned."),
    ]

    with pytest.raises(HTTPException):
        await setup.service.grant(
            ScopeGrantCreateRequest(
                scope_type="team",
                resource_id=uuid.uuid4(),
            ),
            membership_id=setup.target.id,
        )

    setup.resources.require_active.assert_not_awaited()
    setup.repository.add.assert_not_awaited()
    setup.control.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_list_does_not_commit(monkeypatch):
    setup = setup_service(monkeypatch)

    response = await setup.service.list_for(
        membership_id=setup.target.id,
    )

    assert response.membership_id == setup.target.id
    assert response.grants == []
    setup.control.commit.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("removed", [True, False])
async def test_revoke_supports_idempotent_cleanup(monkeypatch, removed):
    setup = setup_service(monkeypatch)
    setup.repository.remove.return_value = removed
    resource_id = uuid.uuid4()

    response = await setup.service.revoke(
        membership_id=setup.target.id,
        scope_type="team",
        resource_id=resource_id,
    )

    assert response.removed is removed
    setup.resources.require_active.assert_not_awaited()
    setup.control.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_commit_failure_rolls_back(monkeypatch):
    setup = setup_service(monkeypatch)
    setup.control.commit.side_effect = RuntimeError("Commit failed.")

    with pytest.raises(RuntimeError, match="Commit failed"):
        await setup.service.revoke(
            membership_id=setup.target.id,
            scope_type="team",
            resource_id=uuid.uuid4(),
        )

    setup.control.rollback.assert_awaited_once()