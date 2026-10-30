from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.dialects import postgresql

from app.modules.employees.organization_repository import (
    ScopedOrganizationRepository,
)
from app.modules.workspace_permissions.access_context import (
    WorkspaceAccessContext,
)


def make_repository():
    department_id = uuid.uuid4()
    team_id = uuid.uuid4()

    context = WorkspaceAccessContext(
        user_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        membership_id=uuid.uuid4(),
        employee_id=uuid.uuid4(),
        role_key="member",
        permissions=frozenset({
            "departments.read",
            "teams.read",
        }),
        scopes=(),
        department_ids=frozenset({department_id}),
        team_ids=frozenset({team_id}),
    )

    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    result.scalars.return_value.all.return_value = []

    session = SimpleNamespace(
        execute=AsyncMock(return_value=result),
        get=AsyncMock(),
    )

    return (
        ScopedOrganizationRepository(session, context),
        session,
        department_id,
        team_id,
    )


def compile_last_statement(session):
    statement = session.execute.await_args.args[0]

    return statement.compile(
        dialect=postgresql.dialect(),
        compile_kwargs={"render_postcompile": True},
    )


@pytest.mark.asyncio
async def test_department_detail_intersects_requested_id_with_scope():
    repository, session, own_department_id, _ = make_repository()
    requested_id = uuid.uuid4()

    assert await repository.get_department_by_id(requested_id) is None

    compiled = compile_last_statement(session)

    assert requested_id in compiled.params.values()
    assert own_department_id in compiled.params.values()
    session.get.assert_not_awaited()


@pytest.mark.asyncio
async def test_team_detail_intersects_requested_id_with_scope():
    repository, session, _, own_team_id = make_repository()
    requested_id = uuid.uuid4()

    assert await repository.get_team_by_id(requested_id) is None

    compiled = compile_last_statement(session)

    assert requested_id in compiled.params.values()
    assert own_team_id in compiled.params.values()
    session.get.assert_not_awaited()


@pytest.mark.asyncio
async def test_inactive_department_option_keeps_scope_filter():
    repository, session, own_department_id, _ = make_repository()

    assert await repository.list_departments(
        include_inactive=True,
    ) == []

    compiled = compile_last_statement(session)

    assert own_department_id in compiled.params.values()


@pytest.mark.asyncio
async def test_team_department_filter_does_not_replace_scope_filter():
    repository, session, _, own_team_id = make_repository()
    requested_department_id = uuid.uuid4()

    assert await repository.list_teams(
        department_id=requested_department_id,
        include_inactive=True,
    ) == []

    compiled = compile_last_statement(session)

    assert requested_department_id in compiled.params.values()
    assert own_team_id in compiled.params.values()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method",
    ["get_department_by_id", "get_team_by_id"],
)
async def test_mutation_lookup_can_lock_scoped_record(method):
    repository, session, _, _ = make_repository()

    await getattr(repository, method)(
        uuid.uuid4(),
        for_update=True,
    )

    compiled = compile_last_statement(session)

    assert "FOR UPDATE" in str(compiled)


@pytest.mark.asyncio
async def test_default_lists_filter_inactive_records():
    repository, session, _, _ = make_repository()

    await repository.list_departments()

    assert "is_active IS true" in str(
        compile_last_statement(session),
    )

    await repository.list_teams()

    assert "is_active IS true" in str(
        compile_last_statement(session),
    )