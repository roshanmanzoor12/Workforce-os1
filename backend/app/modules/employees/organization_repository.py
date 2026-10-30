from __future__ import annotations

import uuid

from sqlalchemy import select

from app.modules.employees.models import Department, Team
from app.modules.employees.organization_policy import (
    department_scope_predicate,
    team_scope_predicate,
)
from app.modules.employees.repository import EmployeeRepository
from app.modules.workspace_permissions.access_context import (
    WorkspaceAccessContext,
)


class ScopedOrganizationRepository(EmployeeRepository):
    def __init__(
        self,
        session,
        context: WorkspaceAccessContext,
    ) -> None:
        super().__init__(session)
        self.context = context

    async def get_department_by_id(
        self,
        department_id: uuid.UUID,
        *,
        for_update: bool = False,
    ) -> Department | None:
        statement = select(Department).where(
            Department.id == department_id,
            department_scope_predicate(self.context),
        )

        if for_update:
            statement = statement.with_for_update(of=Department)

        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_departments(
        self,
        *,
        include_inactive: bool = False,
    ):
        statement = select(Department).where(
            department_scope_predicate(self.context),
        )

        if not include_inactive:
            statement = statement.where(
                Department.is_active.is_(True),
            )

        statement = statement.order_by(
            Department.name.asc(),
            Department.created_at.asc(),
        )

        result = await self.session.execute(statement)
        return result.scalars().all()

    async def get_team_by_id(
        self,
        team_id: uuid.UUID,
        *,
        for_update: bool = False,
    ) -> Team | None:
        statement = select(Team).where(
            Team.id == team_id,
            team_scope_predicate(self.context),
        )

        if for_update:
            statement = statement.with_for_update(of=Team)

        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_teams(
        self,
        *,
        department_id: uuid.UUID | None = None,
        include_inactive: bool = False,
    ):
        statement = select(Team).where(
            team_scope_predicate(self.context),
        )

        if department_id is not None:
            statement = statement.where(
                Team.department_id == department_id,
            )

        if not include_inactive:
            statement = statement.where(
                Team.is_active.is_(True),
            )

        statement = statement.order_by(
            Team.name.asc(),
            Team.created_at.asc(),
        )

        result = await self.session.execute(statement)
        return result.scalars().all()


__all__ = ["ScopedOrganizationRepository"]