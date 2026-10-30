from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.employees.models import Employee
from app.modules.projects.models import Project
from app.modules.projects.service import validate_project_dates
from app.modules.tasks.models import Task
from app.modules.tasks.repository import TaskRepository
from app.modules.tasks.schemas import TaskCreate, TaskUpdate


def apply_task_status(task: Task, status: str) -> None:
    task.status = status
    if status == "done":
        if task.completed_at is None:
            task.completed_at = datetime.now(timezone.utc)
    else:
        task.completed_at = None


class TaskService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = TaskRepository(session)

    async def validate_assignee(self, employee_id: UUID | None) -> None:
        if employee_id is not None:
            employee = await self.session.get(Employee, employee_id)
            if employee is None:
                raise HTTPException(
                    status_code=422,
                    detail="Assignee does not exist in this workspace",
                )

    async def get(self, task_id: UUID) -> Task:
        task = await self.repository.get(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return task

    async def create(self, request: TaskCreate) -> Task:
        project = await self.session.get(Project, request.project_id)
        if project is None:
            raise HTTPException(
                status_code=422,
                detail="Project does not exist in this workspace",
            )

        if project.status in {"completed", "archived"}:
            raise HTTPException(
                status_code=409,
                detail="Cannot add tasks to a completed or archived project",
            )

        await self.validate_assignee(request.assignee_employee_id)
        task = Task(
            **request.model_dump(),
            status="todo",
            completed_at=None,
        )
        return await self.repository.add(task)

    async def list(self, **filters):
        return await self.repository.list(**filters)

    async def update(self, task_id: UUID, request: TaskUpdate) -> Task:
        task = await self.get(task_id)
        changes = request.model_dump(exclude_unset=True)

        validate_project_dates(
            changes.get("start_date", task.start_date),
            changes.get("due_date", task.due_date),
        )

        if "assignee_employee_id" in changes:
            await self.validate_assignee(changes["assignee_employee_id"])

        if "status" in changes:
            apply_task_status(task, changes.pop("status"))

        for field, value in changes.items():
            setattr(task, field, value)

        return await self.repository.save(task)

    async def delete(self, task_id: UUID) -> None:
        task = await self.get(task_id)
        await self.repository.delete(task)