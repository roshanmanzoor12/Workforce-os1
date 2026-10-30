from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.employees.models import Employee
from app.modules.projects.models import Project
from app.modules.projects.repository import ProjectRepository
from app.modules.projects.schemas import ProjectCreate, ProjectUpdate


def validate_project_dates(start_date, due_date) -> None:
    if (
        start_date is not None
        and due_date is not None
        and due_date < start_date
    ):
        raise HTTPException(
            status_code=422,
            detail="due_date cannot precede start_date",
        )


class ProjectService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = ProjectRepository(session)

    async def validate_owner(self, employee_id: UUID | None) -> None:
        if employee_id is not None:
            employee = await self.session.get(Employee, employee_id)
            if employee is None:
                raise HTTPException(
                    status_code=422,
                    detail="Owner employee does not exist in this workspace",
                )

    async def get(self, project_id: UUID) -> Project:
        project = await self.repository.get(project_id)
        if project is None:
            raise HTTPException(status_code=404, detail="Project not found")
        return project

    async def create(self, request: ProjectCreate) -> Project:
        await self.validate_owner(request.owner_employee_id)
        project = Project(
            **request.model_dump(),
            status="planned",
        )
        return await self.repository.add(project)

    async def list(self, **filters):
        return await self.repository.list(**filters)

    async def update(
        self,
        project_id: UUID,
        request: ProjectUpdate,
    ) -> Project:
        project = await self.get(project_id)
        changes = request.model_dump(exclude_unset=True)

        validate_project_dates(
            changes.get("start_date", project.start_date),
            changes.get("due_date", project.due_date),
        )

        if "owner_employee_id" in changes:
            await self.validate_owner(changes["owner_employee_id"])

        for field, value in changes.items():
            setattr(project, field, value)

        return await self.repository.save(project)

    async def delete(self, project_id: UUID) -> None:
        from app.modules.tasks.models import Task

        project = await self.get(project_id)
        task_count = await self.session.scalar(
            select(func.count())
            .select_from(Task)
            .where(Task.project_id == project_id)
        )

        if task_count:
            raise HTTPException(
                status_code=409,
                detail="Project has tasks; archive it or remove its tasks first",
            )

        await self.repository.delete(project)