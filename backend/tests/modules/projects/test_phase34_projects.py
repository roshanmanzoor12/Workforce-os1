from datetime import date
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.modules.projects.models import Project
from app.modules.projects.schemas import ProjectCreate, ProjectUpdate
from app.modules.projects.service import ProjectService


def test_project_rejects_blank_name():
    with pytest.raises(ValueError):
        ProjectCreate(name="   ")


def test_project_rejects_reversed_dates():
    with pytest.raises(ValueError):
        ProjectCreate(
            name="Website",
            start_date=date(2026, 10, 10),
            due_date=date(2026, 10, 1),
        )


def test_project_rejects_client_workspace_id():
    with pytest.raises(ValueError):
        ProjectCreate(name="Website", workspace_id=uuid4())


@pytest.mark.parametrize("field", ["name", "status"])
def test_project_update_rejects_null_required_fields(field):
    with pytest.raises(ValueError):
        ProjectUpdate(**{field: None})


@pytest.mark.asyncio
async def test_missing_project_returns_404():
    service = ProjectService(AsyncMock())
    service.repository = AsyncMock()
    service.repository.get.return_value = None

    with pytest.raises(HTTPException) as error:
        await service.get(uuid4())

    assert error.value.status_code == 404


@pytest.mark.asyncio
async def test_missing_owner_prevents_project_creation():
    session = AsyncMock()
    session.get.return_value = None
    service = ProjectService(session)
    service.repository = AsyncMock()

    with pytest.raises(HTTPException) as error:
        await service.create(
            ProjectCreate(name="Website", owner_employee_id=uuid4())
        )

    assert error.value.status_code == 422
    service.repository.add.assert_not_awaited()


@pytest.mark.asyncio
async def test_partial_date_update_checks_existing_start_date():
    service = ProjectService(AsyncMock())
    service.repository = AsyncMock()
    service.repository.get.return_value = Project(
        name="Website",
        start_date=date(2026, 10, 10),
        due_date=date(2026, 10, 20),
        status="planned",
    )

    with pytest.raises(HTTPException) as error:
        await service.update(
            uuid4(),
            ProjectUpdate(due_date=date(2026, 10, 1)),
        )

    assert error.value.status_code == 422
    service.repository.save.assert_not_awaited()


@pytest.mark.asyncio
async def test_project_with_tasks_cannot_be_deleted():
    session = AsyncMock()
    session.scalar.return_value = 1
    service = ProjectService(session)
    service.repository = AsyncMock()
    service.repository.get.return_value = Project(name="Website")

    with pytest.raises(HTTPException) as error:
        await service.delete(uuid4())

    assert error.value.status_code == 409
    service.repository.delete.assert_not_awaited()