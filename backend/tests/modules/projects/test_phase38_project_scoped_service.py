from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.modules.projects.schemas import ProjectCreate, ProjectUpdate
from app.modules.projects.scoped_service import ScopedProjectService
from app.modules.workspace_permissions.access_context import (
    WorkspaceAccessContext,
)
from app.modules.workspace_permissions.scopes import (
    self_scope,
    workspace_scope,
)


def make_service(*, permissions=None, workspace=False):
    employee_id = uuid4()

    context = WorkspaceAccessContext(
        user_id=uuid4(),
        workspace_id=uuid4(),
        membership_id=uuid4(),
        employee_id=employee_id,
        role_key="member",
        permissions=(
            frozenset({"projects.view", "projects.manage"})
            if permissions is None
            else permissions
        ),
        scopes=(
            (workspace_scope(),)
            if workspace
            else (self_scope(),)
        ),
    )

    session = SimpleNamespace(
        scalar=AsyncMock(return_value=employee_id),
    )
    service = ScopedProjectService(session, context)
    service.repository = AsyncMock()
    return service


@pytest.mark.asyncio
async def test_get_uses_resource_predicate():
    service = make_service()
    project_id = uuid4()
    expected = SimpleNamespace(id=project_id)
    service.repository.get.return_value = expected

    result = await service.get(project_id)

    assert result is expected
    service.repository.get.assert_awaited_once_with(
        project_id,
        access_predicate=service.access_predicate,
    )


@pytest.mark.asyncio
async def test_inaccessible_project_returns_404():
    service = make_service()
    service.repository.get.return_value = None

    with pytest.raises(HTTPException) as error:
        await service.get(uuid4())

    assert error.value.status_code == 404


@pytest.mark.asyncio
async def test_list_filters_before_repository_pagination():
    service = make_service()
    service.repository.list.return_value = ([], 0)

    result = await service.list(offset=25, limit=10, status="active")

    assert result == ([], 0)
    service.repository.list.assert_awaited_once_with(
        offset=25,
        limit=10,
        status="active",
        access_predicate=service.access_predicate,
    )


@pytest.mark.asyncio
async def test_caller_cannot_replace_access_predicate():
    service = make_service()

    with pytest.raises(HTTPException) as error:
        await service.list(access_predicate=True)

    assert error.value.status_code == 422
    service.repository.list.assert_not_awaited()


@pytest.mark.asyncio
async def test_missing_read_permission_denies_list():
    service = make_service(permissions=frozenset())

    with pytest.raises(HTTPException) as error:
        await service.list()

    assert error.value.status_code == 403
    service.repository.list.assert_not_awaited()


@pytest.mark.asyncio
async def test_read_only_member_cannot_create():
    service = make_service(
        permissions=frozenset({"projects.view"})
    )

    with pytest.raises(HTTPException) as error:
        await service.create(
            ProjectCreate(
                name="Website",
                owner_employee_id=service.context.employee_id,
            )
        )

    assert error.value.status_code == 403
    service.repository.add.assert_not_awaited()


@pytest.mark.asyncio
async def test_self_scope_cannot_create_unowned_project():
    service = make_service()

    with pytest.raises(HTTPException) as error:
        await service.create(ProjectCreate(name="Website"))

    assert error.value.status_code == 403
    service.repository.add.assert_not_awaited()


@pytest.mark.asyncio
async def test_outside_owner_prevents_create():
    service = make_service()
    service.session.scalar.return_value = None

    with pytest.raises(HTTPException) as error:
        await service.create(
            ProjectCreate(
                name="Website",
                owner_employee_id=uuid4(),
            )
        )

    assert error.value.status_code == 403
    service.repository.add.assert_not_awaited()


@pytest.mark.asyncio
async def test_workspace_scope_can_create_unowned_project():
    service = make_service(workspace=True)

    await service.create(ProjectCreate(name="Website"))

    service.repository.add.assert_awaited_once()
    service.session.scalar.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_denies_inaccessible_project_before_mutation():
    service = make_service()
    service.repository.get.return_value = None

    with pytest.raises(HTTPException) as error:
        await service.update(
            uuid4(),
            ProjectUpdate(name="Changed"),
        )

    assert error.value.status_code == 404
    service.repository.save.assert_not_awaited()


@pytest.mark.asyncio
async def test_owner_reassignment_outside_scope_is_denied():
    service = make_service()
    project = SimpleNamespace(
        name="Website",
        start_date=None,
        due_date=None,
        owner_employee_id=service.context.employee_id,
    )
    service.repository.get.return_value = project
    service.session.scalar.return_value = None

    with pytest.raises(HTTPException) as error:
        await service.update(
            uuid4(),
            ProjectUpdate(owner_employee_id=uuid4()),
        )

    assert error.value.status_code == 403
    assert project.owner_employee_id == service.context.employee_id
    service.repository.save.assert_not_awaited()


@pytest.mark.asyncio
async def test_read_only_member_cannot_delete():
    service = make_service(
        permissions=frozenset({"projects.view"})
    )

    with pytest.raises(HTTPException) as error:
        await service.delete(uuid4())

    assert error.value.status_code == 403
    service.repository.get.assert_not_awaited()
    service.repository.delete.assert_not_awaited()