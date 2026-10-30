from __future__ import annotations

import importlib
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.modules.workspace_rbac.scope_schemas import (
    ScopeGrantCreateRequest,
)


routes = importlib.import_module(
    "app.modules.workspace_rbac.scope_router",
)


@pytest.mark.asyncio
async def test_list_forwards_target_membership():
    membership_id = uuid.uuid4()
    expected = object()
    service = SimpleNamespace(
        list_for=AsyncMock(return_value=expected),
    )

    result = await routes.list_member_scopes(
        membership_id,
        service,
    )

    assert result is expected
    service.list_for.assert_awaited_once_with(
        membership_id=membership_id,
    )


@pytest.mark.asyncio
async def test_grant_forwards_validated_payload():
    membership_id = uuid.uuid4()

    payload = ScopeGrantCreateRequest(
        scope_type="team",
        resource_id=uuid.uuid4(),
    )

    expected = object()
    service = SimpleNamespace(
        grant=AsyncMock(return_value=expected),
    )

    result = await routes.grant_member_scope(
        membership_id,
        payload,
        service,
    )

    assert result is expected
    service.grant.assert_awaited_once_with(
        payload,
        membership_id=membership_id,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("scope_type", ["department", "team"])
async def test_revoke_forwards_exact_resource(scope_type):
    membership_id = uuid.uuid4()
    resource_id = uuid.uuid4()
    expected = object()

    service = SimpleNamespace(
        revoke=AsyncMock(return_value=expected),
    )

    result = await routes.revoke_member_scope(
        membership_id,
        scope_type,
        resource_id,
        service,
    )

    assert result is expected

    service.revoke.assert_awaited_once_with(
        membership_id=membership_id,
        scope_type=scope_type,
        resource_id=resource_id,
    )