from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.dialects import postgresql

from app.core.exceptions import ResourceNotFound, ValidationError
from app.modules.workspace_rbac.scope_repository import (
    MembershipScopeGrantRepository,
)


def membership(workspace_id, membership_id, *, status="active"):
    return SimpleNamespace(
        id=membership_id,
        workspace_id=workspace_id,
        status=status,
    )


def sql(statement):
    return str(statement.compile(dialect=postgresql.dialect()))


@pytest.mark.parametrize(
    "scope_type",
    ["workspace", "self", "company", "TEAM", "", None],
)
def test_invalid_scope_type_is_rejected(scope_type):
    with pytest.raises(ValidationError):
        MembershipScopeGrantRepository.validate_scope_type(scope_type)


@pytest.mark.parametrize("scope_type", ["department", "team"])
def test_supported_scope_type(scope_type):
    assert (
        MembershipScopeGrantRepository.validate_scope_type(scope_type)
        == scope_type
    )


@pytest.mark.asyncio
async def test_cross_workspace_membership_is_rejected():
    workspace_id = uuid.uuid4()
    membership_id = uuid.uuid4()

    session = SimpleNamespace(
        scalar=AsyncMock(
            return_value=membership(uuid.uuid4(), membership_id),
        ),
    )

    repository = MembershipScopeGrantRepository(session)

    with pytest.raises(ResourceNotFound):
        await repository.require_membership(
            workspace_id=workspace_id,
            membership_id=membership_id,
        )


@pytest.mark.asyncio
async def test_inactive_membership_is_rejected_for_grant():
    workspace_id = uuid.uuid4()
    membership_id = uuid.uuid4()

    session = SimpleNamespace(
        scalar=AsyncMock(
            return_value=membership(
                workspace_id,
                membership_id,
                status="suspended",
            ),
        ),
    )

    repository = MembershipScopeGrantRepository(session)

    with pytest.raises(ResourceNotFound):
        await repository.add(
            workspace_id=workspace_id,
            membership_id=membership_id,
            scope_type="team",
            resource_id=uuid.uuid4(),
            granted_by_user_id=uuid.uuid4(),
        )

    assert session.scalar.await_count == 1


@pytest.mark.asyncio
async def test_list_query_is_workspace_and_membership_bound():
    workspace_id = uuid.uuid4()
    membership_id = uuid.uuid4()

    result = MagicMock()
    result.scalars.return_value.all.return_value = []

    session = SimpleNamespace(execute=AsyncMock(return_value=result))
    repository = MembershipScopeGrantRepository(session)

    assert await repository.list_for(
        workspace_id=workspace_id,
        membership_id=membership_id,
    ) == ()

    statement = session.execute.await_args.args[0]
    compiled = statement.compile(dialect=postgresql.dialect())

    assert workspace_id in compiled.params.values()
    assert membership_id in compiled.params.values()
    assert "workspace_memberships.status" in str(compiled)
    assert "ORDER BY" in str(compiled)


@pytest.mark.asyncio
async def test_add_locks_membership_and_uses_conflict_safe_insert():
    workspace_id = uuid.uuid4()
    membership_id = uuid.uuid4()
    resource_id = uuid.uuid4()
    grantor_id = uuid.uuid4()
    created = object()

    session = SimpleNamespace(
        scalar=AsyncMock(
            side_effect=[
                membership(workspace_id, membership_id),
                created,
            ],
        ),
    )

    repository = MembershipScopeGrantRepository(session)

    result = await repository.add(
        workspace_id=workspace_id,
        membership_id=membership_id,
        scope_type="team",
        resource_id=resource_id,
        granted_by_user_id=grantor_id,
    )

    assert result is created

    calls = session.scalar.await_args_list

    assert "FOR UPDATE" in sql(calls[0].args[0])
    assert "ON CONFLICT" in sql(calls[1].args[0])
    assert "DO NOTHING" in sql(calls[1].args[0])


@pytest.mark.asyncio
async def test_existing_grant_retains_original_record():
    workspace_id = uuid.uuid4()
    membership_id = uuid.uuid4()
    existing = object()

    session = SimpleNamespace(
        scalar=AsyncMock(
            side_effect=[
                membership(workspace_id, membership_id),
                None,
                existing,
            ],
        ),
    )

    repository = MembershipScopeGrantRepository(session)

    result = await repository.add(
        workspace_id=workspace_id,
        membership_id=membership_id,
        scope_type="department",
        resource_id=uuid.uuid4(),
        granted_by_user_id=uuid.uuid4(),
    )

    assert result is existing


@pytest.mark.asyncio
@pytest.mark.parametrize("found", [True, False])
async def test_remove_is_workspace_bound_and_idempotent(found):
    workspace_id = uuid.uuid4()
    membership_id = uuid.uuid4()
    resource_id = uuid.uuid4()

    session = SimpleNamespace(
        scalar=AsyncMock(
            side_effect=[
                membership(
                    workspace_id,
                    membership_id,
                    status="suspended",
                ),
                resource_id if found else None,
            ],
        ),
    )

    repository = MembershipScopeGrantRepository(session)

    assert await repository.remove(
        workspace_id=workspace_id,
        membership_id=membership_id,
        scope_type="team",
        resource_id=resource_id,
    ) is found

    statement = session.scalar.await_args_list[1].args[0]
    compiled = statement.compile(dialect=postgresql.dialect())

    assert "EXISTS" in str(compiled)
    assert workspace_id in compiled.params.values()
    assert membership_id in compiled.params.values()
    assert resource_id in compiled.params.values()