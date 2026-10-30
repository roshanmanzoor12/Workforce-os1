from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.dialects import postgresql

from app.modules.employees.scope_access import build_employee_access
from app.modules.employees.scoped_repository import (
    ScopedEmployeeRepository,
)


def make_repository():
    scope = SimpleNamespace(
        workspace_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        membership_id=uuid.uuid4(),
        role_key="member",
        effective_permissions=frozenset({"employees.self.read"}),
    )

    employee = SimpleNamespace(
        id=uuid.uuid4(),
        user_id=scope.user_id,
        team_id=None,
        department_id=None,
        is_active=True,
        employment_status="active",
    )

    context = build_employee_access(scope, employee)
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    result.scalars.return_value.all.return_value = []

    session = SimpleNamespace(
        execute=AsyncMock(return_value=result),
        get=AsyncMock(),
    )

    return ScopedEmployeeRepository(session, context), employee


def compiled(statement):
    return statement.compile(dialect=postgresql.dialect())


@pytest.mark.asyncio
async def test_detail_query_intersects_target_with_self_scope():
    repository, own = make_repository()
    target = uuid.uuid4()

    assert await repository.get_employee_by_id(target) is None

    statement = repository.session.execute.await_args.args[0]
    query = compiled(statement)

    assert own.id in query.params.values()
    assert target in query.params.values()

    repository.session.get.assert_not_awaited()


@pytest.mark.asyncio
async def test_list_filter_cannot_replace_self_scope():
    repository, own = make_repository()
    unrelated_team = uuid.uuid4()

    assert await repository.list_employees(
        team_id=unrelated_team,
        search="example",
        include_inactive=True,
    ) == []

    statement = repository.session.execute.await_args.args[0]
    query = compiled(statement)

    assert own.id in query.params.values()
    assert unrelated_team in query.params.values()
    assert "%example%" in query.params.values()


@pytest.mark.asyncio
async def test_mutation_query_locks_the_scoped_target():
    repository, own = make_repository()

    await repository.get_employee_by_id(
        own.id,
        for_update=True,
    )

    statement = repository.session.execute.await_args.args[0]
    query = compiled(statement)

    assert "FOR UPDATE" in str(query)
    assert own.id in query.params.values()


@pytest.mark.asyncio
async def test_user_lookup_is_also_scoped():
    repository, own = make_repository()
    other_user = uuid.uuid4()

    await repository.get_employee_by_user_id(other_user)

    statement = repository.session.execute.await_args.args[0]
    query = compiled(statement)

    assert own.id in query.params.values()
    assert other_user in query.params.values()