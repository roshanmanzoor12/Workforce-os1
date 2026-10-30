from __future__ import annotations

import importlib
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.dialects import postgresql

from app.modules.workspace_permissions.access_context import (
    WorkspaceAccessContext,
)
from app.modules.workspace_permissions.scopes import (
    WorkspaceResourceScope,
    WorkspaceScopeType,
)
from app.modules.workspace_rbac.scope_resources import (
    TenantScopeResourceValidator,
)
from app.modules.workspace_rbac.scope_schemas import (
    ScopeGrantCreateRequest,
)


saved = importlib.import_module(
    "app.modules.workspace_permissions.saved_scopes",
)


def context():
    return WorkspaceAccessContext(
        user_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        membership_id=uuid.uuid4(),
        employee_id=uuid.uuid4(),
        role_key="member",
        permissions=frozenset({"employees.read"}),
        scopes=(
            WorkspaceResourceScope(WorkspaceScopeType.SELF),
        ),
    )


def grant(access, *, scope_type="team", resource_id=None):
    return SimpleNamespace(
        membership_id=access.membership_id,
        scope_type=scope_type,
        resource_id=resource_id or uuid.uuid4(),
    )


def setup_resolution(monkeypatch):
    access = context()

    scope = SimpleNamespace(
        workspace_id=access.workspace_id,
        user_id=access.user_id,
        membership_id=access.membership_id,
        session=object(),
    )

    membership = SimpleNamespace(
        id=access.membership_id,
        workspace_id=access.workspace_id,
        user_id=access.user_id,
        status="active",
        role_key="member",
    )

    repository = SimpleNamespace(
        require_workspace=AsyncMock(),
        require_membership=AsyncMock(return_value=membership),
        list_for=AsyncMock(return_value=()),
    )

    resources = SimpleNamespace(is_active=AsyncMock(return_value=True))
    permissions = AsyncMock(return_value=access.permissions)

    monkeypatch.setattr(
        saved,
        "MembershipScopeGrantRepository",
        lambda session: repository,
    )

    monkeypatch.setattr(
        saved,
        "TenantScopeResourceValidator",
        lambda **kwargs: resources,
    )

    monkeypatch.setattr(
        saved,
        "resolve_membership_permissions",
        permissions,
    )

    return SimpleNamespace(
        access=access,
        scope=scope,
        membership=membership,
        repository=repository,
        resources=resources,
        permissions=permissions,
    )


def test_merge_preserves_permissions_and_identity():
    access = context()
    team = grant(access)

    result = saved.merge_saved_scopes(access, (team,))

    assert result.permissions == access.permissions
    assert result.user_id == access.user_id
    assert result.membership_id == access.membership_id
    assert result.workspace_id == access.workspace_id
    assert result.employee_id == access.employee_id
    assert not result.is_workspace_scoped
    assert result.scope_ids(WorkspaceScopeType.TEAM) == {
        team.resource_id,
    }

    # The input remains immutable.
    assert access.scope_ids(WorkspaceScopeType.TEAM) == frozenset()


def test_merge_deduplicates_scope_grants():
    access = context()
    team = grant(access)

    result = saved.merge_saved_scopes(access, (team, team))

    assert len(result.scopes) == 2


@pytest.mark.parametrize("scope_type", ["workspace", "self", "shared"])
def test_saved_grants_cannot_create_broad_or_unsupported_scope(scope_type):
    access = context()

    with pytest.raises(HTTPException) as error:
        saved.merge_saved_scopes(
            access,
            (grant(access, scope_type=scope_type),),
        )

    assert error.value.status_code == 403


def test_cross_membership_grant_is_rejected():
    access = context()
    wrong = grant(access)
    wrong.membership_id = uuid.uuid4()

    with pytest.raises(HTTPException):
        saved.merge_saved_scopes(access, (wrong,))


def test_request_cannot_supply_grantor_identity():
    with pytest.raises(PydanticValidationError):
        ScopeGrantCreateRequest(
            scope_type="team",
            resource_id=uuid.uuid4(),
            granted_by_user_id=uuid.uuid4(),
        )


def test_resource_validator_rejects_wrong_workspace():
    with pytest.raises(HTTPException):
        TenantScopeResourceValidator(
            workspace_id=uuid.uuid4(),
            tenant_scope=SimpleNamespace(
                workspace_id=uuid.uuid4(),
                session=object(),
            ),
        )


@pytest.mark.asyncio
@pytest.mark.parametrize("scope_type", ["department", "team"])
async def test_resource_lookup_requires_active_row(scope_type):
    workspace_id = uuid.uuid4()
    resource_id = uuid.uuid4()
    session = SimpleNamespace(
        scalar=AsyncMock(return_value=resource_id),
    )

    validator = TenantScopeResourceValidator(
        workspace_id=workspace_id,
        tenant_scope=SimpleNamespace(
            workspace_id=workspace_id,
            session=session,
        ),
    )

    assert await validator.is_active(
        scope_type=scope_type,
        resource_id=resource_id,
    )

    statement = session.scalar.await_args.args[0]
    compiled = statement.compile(dialect=postgresql.dialect())

    assert resource_id in compiled.params.values()
    assert "is_active IS true" in str(compiled)


@pytest.mark.asyncio
async def test_resolution_merges_only_active_resources(monkeypatch):
    setup = setup_resolution(monkeypatch)
    active = grant(setup.access)
    inactive = grant(setup.access, scope_type="department")

    setup.repository.list_for.return_value = (active, inactive)
    setup.resources.is_active.side_effect = [True, False]

    result = await saved.resolve_saved_scope_access(
        object(),
        tenant_scope=setup.scope,
        context=setup.access,
    )

    assert result.scope_ids(WorkspaceScopeType.TEAM) == {
        active.resource_id,
    }
    assert result.scope_ids(WorkspaceScopeType.DEPARTMENT) == frozenset()
    assert result.permissions == setup.access.permissions


@pytest.mark.asyncio
async def test_identity_mismatch_stops_control_queries(monkeypatch):
    setup = setup_resolution(monkeypatch)
    setup.scope.user_id = uuid.uuid4()

    with pytest.raises(HTTPException):
        await saved.resolve_saved_scope_access(
            object(),
            tenant_scope=setup.scope,
            context=setup.access,
        )

    setup.repository.require_workspace.assert_not_awaited()


@pytest.mark.asyncio
async def test_stale_permissions_stop_scope_resolution(monkeypatch):
    setup = setup_resolution(monkeypatch)
    setup.permissions.return_value = frozenset()

    with pytest.raises(HTTPException):
        await saved.resolve_saved_scope_access(
            object(),
            tenant_scope=setup.scope,
            context=setup.access,
        )

    setup.repository.list_for.assert_not_awaited()
    setup.resources.is_active.assert_not_awaited()


@pytest.mark.asyncio
async def test_membership_user_mismatch_is_rejected(monkeypatch):
    setup = setup_resolution(monkeypatch)
    setup.membership.user_id = uuid.uuid4()

    with pytest.raises(HTTPException):
        await saved.resolve_saved_scope_access(
            object(),
            tenant_scope=setup.scope,
            context=setup.access,
        )

    setup.permissions.assert_not_awaited()
    setup.repository.list_for.assert_not_awaited()


@pytest.mark.asyncio
async def test_banned_membership_denial_is_preserved(monkeypatch):
    setup = setup_resolution(monkeypatch)

    setup.permissions.side_effect = HTTPException(
        status_code=403,
        detail="Workspace access is banned.",
    )

    with pytest.raises(HTTPException) as error:
        await saved.resolve_saved_scope_access(
            object(),
            tenant_scope=setup.scope,
            context=setup.access,
        )

    assert error.value.status_code == 403
    setup.repository.list_for.assert_not_awaited()