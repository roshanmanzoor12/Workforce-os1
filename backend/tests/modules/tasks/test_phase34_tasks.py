from datetime import date
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.modules.projects.models import Project
from app.modules.tasks.models import Task
from app.modules.tasks.schemas import TaskCreate, TaskUpdate
from app.modules.tasks.service import TaskService, apply_task_status


def test_task_requires_project():
    with pytest.raises(ValueError):
        TaskCreate(title="Build homepage")


def test_task_rejects_blank_title():
    with pytest.raises(ValueError):
        TaskCreate(project_id=uuid4(), title="   ")


def test_task_rejects_invalid_dates():
    with pytest.raises(ValueError):
        TaskCreate(
            project_id=uuid4(),
            title="Build homepage",
            start_date=date(2026, 10, 10),
            due_date=date(2026, 10, 1),
        )


def test_task_rejects_client_completion_timestamp():
    with pytest.raises(ValueError):
        TaskUpdate(completed_at="2026-10-01T00:00:00Z")


@pytest.mark.parametrize("field", ["title", "status", "priority"])
def test_task_update_rejects_null_required_fields(field):
    with pytest.raises(ValueError):
        TaskUpdate(**{field: None})


def test_completion_and_reopening():
    task = Task(title="Build homepage", project_id=uuid4())
    apply_task_status(task, "done")

    completed_at = task.completed_at
    assert completed_at is not None
    assert completed_at.tzinfo is not None

    apply_task_status(task, "done")
    assert task.completed_at == completed_at

    apply_task_status(task, "in_progress")
    assert task.completed_at is None


@pytest.mark.asyncio
async def test_unknown_project_prevents_task_creation():
    session = AsyncMock()
    session.get.return_value = None
    service = TaskService(session)
    service.repository = AsyncMock()

    with pytest.raises(HTTPException) as error:
        await service.create(
            TaskCreate(project_id=uuid4(), title="Build homepage")
        )

    assert error.value.status_code == 422
    service.repository.add.assert_not_awaited()


@pytest.mark.asyncio
async def test_archived_project_prevents_task_creation():
    session = AsyncMock()
    session.get.return_value = Project(name="Website", status="archived")
    service = TaskService(session)
    service.repository = AsyncMock()

    with pytest.raises(HTTPException) as error:
        await service.create(
            TaskCreate(project_id=uuid4(), title="Build homepage")
        )

    assert error.value.status_code == 409
    service.repository.add.assert_not_awaited()


@pytest.mark.asyncio
async def test_missing_assignee_prevents_task_creation():
    session = AsyncMock()
    session.get.side_effect = [
        Project(name="Website", status="active"),
        None,
    ]
    service = TaskService(session)
    service.repository = AsyncMock()

    with pytest.raises(HTTPException) as error:
        await service.create(
            TaskCreate(
                project_id=uuid4(),
                title="Build homepage",
                assignee_employee_id=uuid4(),
            )
        )

    assert error.value.status_code == 422
    service.repository.add.assert_not_awaited()


@pytest.mark.asyncio
async def test_missing_task_returns_404():
    service = TaskService(AsyncMock())
    service.repository = AsyncMock()
    service.repository.get.return_value = None

    with pytest.raises(HTTPException) as error:
        await service.get(uuid4())

    assert error.value.status_code == 404