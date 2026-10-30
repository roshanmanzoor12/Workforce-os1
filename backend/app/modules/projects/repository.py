from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.projects.models import Project


class ProjectRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(
        self,
        project_id: UUID,
        *,
        access_predicate=None,
    ) -> Project | None:
        if access_predicate is None:
            return await self.session.get(Project, project_id)

        statement = (
            select(Project)
            .where(Project.id == project_id)
            .where(access_predicate)
        )

        return await self.session.scalar(statement)

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
        status: str | None = None,
        access_predicate=None,
    ) -> tuple[list[Project], int]:
        statement = select(Project)
        count_statement = select(func.count()).select_from(Project)

        if access_predicate is not None:
            statement = statement.where(access_predicate)
            count_statement = count_statement.where(access_predicate)

        if status is not None:
            statement = statement.where(Project.status == status)
            count_statement = count_statement.where(Project.status == status)

        total = int(await self.session.scalar(count_statement) or 0)

        result = await self.session.scalars(
            statement
            .order_by(Project.created_at.desc(), Project.id)
            .offset(offset)
            .limit(limit)
        )

        return list(result.all()), total

    async def add(self, project: Project) -> Project:
        self.session.add(project)
        await self.session.flush()
        await self.session.refresh(project)
        return project

    async def save(self, project: Project) -> Project:
        await self.session.flush()
        await self.session.refresh(project)
        return project

    async def delete(self, project: Project) -> None:
        await self.session.delete(project)
        await self.session.flush()