from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.tasks.models import Task


class TaskRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, task_id: UUID) -> Task | None:
        return await self.session.get(Task, task_id)

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
        project_id: UUID | None = None,
        assignee_employee_id: UUID | None = None,
        status: str | None = None,
    ) -> tuple[list[Task], int]:
        conditions = []

        if project_id is not None:
            conditions.append(Task.project_id == project_id)
        if assignee_employee_id is not None:
            conditions.append(
                Task.assignee_employee_id == assignee_employee_id
            )
        if status is not None:
            conditions.append(Task.status == status)

        total = int(
            await self.session.scalar(
                select(func.count()).select_from(Task).where(*conditions)
            )
            or 0
        )
        result = await self.session.scalars(
            select(Task)
            .where(*conditions)
            .order_by(Task.created_at.desc(), Task.id)
            .offset(offset)
            .limit(limit)
        )
        return list(result.all()), total

    async def add(self, task: Task) -> Task:
        self.session.add(task)
        await self.session.flush()
        await self.session.refresh(task)
        return task

    async def save(self, task: Task) -> Task:
        await self.session.flush()
        await self.session.refresh(task)
        return task

    async def delete(self, task: Task) -> None:
        await self.session.delete(task)
        await self.session.flush()