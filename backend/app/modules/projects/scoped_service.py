from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.employees.models import (
    EMPLOYMENT_STATUS_ACTIVE,
    Employee,
)
from app.modules.projects.access import (
    employee_scope_predicate,
    project_scope_predicate,
    require_project_context,
)
from app.modules.projects.models import Project
from app.modules.projects.schemas import ProjectCreate, ProjectUpdate
from app.modules.projects.service import ProjectService
from app.modules.workspace_permissions.access_context import (
    WorkspaceAccessContext,
)


class ScopedProjectService(ProjectService):
    """
    ProjectService with enforced permission and resource boundaries.

    Existing date validation, task deletion checks, and repository
    behavior remain in the base business service.
    """

    def __init__(
        self,
        session: AsyncSession,
        context: WorkspaceAccessContext,
    ):
        super().__init__(session)
        self.context = context
        self.access_predicate = project_scope_predicate(context)

    async def _require_visible(self, project_id: UUID) -> Project:
        project = await self.repository.get(
            project_id,
            access_predicate=self.access_predicate,
        )

        if project is None:
            raise HTTPException(
                status_code=404,
                detail="Project not found",
            )

        return project

    async def get(self, project_id: UUID) -> Project:
        # Management permits the internal get used by update/delete.
        if not (
            self.context.has_permission("projects.view")
            or self.context.has_permission("projects.manage")
        ):
            require_project_context(self.context)

        return await self._require_visible(project_id)

    async def validate_owner(self, employee_id: UUID | None) -> None:
        if employee_id is None:
            if self.context.is_workspace_scoped:
                return

            raise HTTPException(
                status_code=403,
                detail=(
                    "A project within your scope requires "
                    "an accessible owner employee."
                ),
            )

        employee = await self.session.scalar(
            select(Employee.id)
            .where(
                Employee.id == employee_id,
                Employee.is_active.is_(True),
                Employee.employment_status == EMPLOYMENT_STATUS_ACTIVE,
            )
            .where(employee_scope_predicate(self.context))
        )

        if employee is None:
            raise HTTPException(
                status_code=403,
                detail="Project owner employee is outside your access scope.",
            )

    async def create(self, request: ProjectCreate) -> Project:
        require_project_context(self.context, manage=True)
        return await super().create(request)

    async def list(self, **filters):
        require_project_context(self.context)

        if "access_predicate" in filters:
            raise HTTPException(
                status_code=422,
                detail="Project access filters are controlled by the backend.",
            )

        return await self.repository.list(
            **filters,
            access_predicate=self.access_predicate,
        )

    async def update(
        self,
        project_id: UUID,
        request: ProjectUpdate,
    ) -> Project:
        require_project_context(self.context, manage=True)
        return await super().update(project_id, request)

    async def delete(self, project_id: UUID) -> None:
        require_project_context(self.context, manage=True)
        await super().delete(project_id)


__all__ = ["ScopedProjectService"]