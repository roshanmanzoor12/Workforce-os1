from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql

from app.modules.projects.access import project_scope_predicate
from app.modules.projects.repository import ProjectRepository
from app.modules.workspace_permissions.access_context import (
    WorkspaceAccessContext,
)
from app.modules.workspace_permissions.scopes import self_scope


def access():
    return WorkspaceAccessContext(
        user_id=uuid4(),
        workspace_id=uuid4(),
        membership_id=uuid4(),
        employee_id=uuid4(),
        role_key="member",
        permissions=frozenset({"projects.view"}),
        scopes=(self_scope(),),
    )


def sql(statement):
    return str(
        statement.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )


@pytest.mark.asyncio
async def test_count_and_page_use_same_scope_filter():
    context = access()
    predicate = project_scope_predicate(context)
    session = SimpleNamespace(
        scalar=AsyncMock(return_value=2),
        scalars=AsyncMock(
            return_value=SimpleNamespace(all=lambda: [])
        ),
    )

    result = await ProjectRepository(session).list(
        offset=10,
        limit=5,
        status="active",
        access_predicate=predicate,
    )

    assert result == ([], 2)

    count_sql = sql(session.scalar.await_args.args[0])
    page_sql = sql(session.scalars.await_args.args[0])

    for statement in (count_sql, page_sql):
        assert "owner_employee_id IN" in statement
        assert str(context.employee_id) in statement
        assert "projects.status = 'active'" in statement

    assert "LIMIT 5" in page_sql
    assert "OFFSET 10" in page_sql
    assert "LIMIT" not in count_sql
    assert "OFFSET" not in count_sql


@pytest.mark.asyncio
async def test_scoped_get_does_not_use_identity_map_shortcut():
    context = access()
    project_id = uuid4()
    session = SimpleNamespace(
        scalar=AsyncMock(return_value=None),
        get=AsyncMock(),
    )

    result = await ProjectRepository(session).get(
        project_id,
        access_predicate=project_scope_predicate(context),
    )

    assert result is None
    session.get.assert_not_awaited()

    statement = sql(session.scalar.await_args.args[0])
    assert str(project_id) in statement
    assert str(context.employee_id) in statement
    assert "owner_employee_id IN" in statement


@pytest.mark.asyncio
async def test_unscoped_repository_contract_is_preserved():
    project_id = uuid4()
    expected = SimpleNamespace(id=project_id)
    session = SimpleNamespace(
        get=AsyncMock(return_value=expected),
    )

    result = await ProjectRepository(session).get(project_id)

    assert result is expected
    session.get.assert_awaited_once()