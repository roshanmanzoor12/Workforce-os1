from __future__ import annotations

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from app.modules.employees.models import Employee
from app.modules.employees.repository import EmployeeRepository
from app.modules.employees.scope_access import (
    employee_scope_predicate,
)
from app.modules.workspace_permissions.access_context import (
    WorkspaceAccessContext,
)


class ScopedEmployeeRepository(EmployeeRepository):
    def __init__(
        self,
        session,
        context: WorkspaceAccessContext,
    ) -> None:
        super().__init__(session)
        self.context = context

    def _employee_statement(self):
        return (
            select(Employee)
            .options(
                selectinload(Employee.department),
                selectinload(Employee.team),
            )
            .where(employee_scope_predicate(self.context))
        )

    async def get_employee_by_id(
        self,
        employee_id: uuid.UUID,
        *,
        for_update: bool = False,
    ) -> Employee | None:
        statement = self._employee_statement().where(
            Employee.id == employee_id
        )

        if for_update:
            statement = statement.with_for_update(of=Employee)

        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_employee_by_user_id(
        self,
        user_id: uuid.UUID,
    ) -> Employee | None:
        statement = self._employee_statement().where(
            Employee.user_id == user_id
        )

        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_employees(
        self,
        *,
        department_id: uuid.UUID | None = None,
        team_id: uuid.UUID | None = None,
        manager_id: uuid.UUID | None = None,
        employment_status: str | None = None,
        include_inactive: bool = False,
        search: str | None = None,
    ):
        statement = self._employee_statement()

        if department_id is not None:
            statement = statement.where(
                Employee.department_id == department_id
            )

        if team_id is not None:
            statement = statement.where(
                Employee.team_id == team_id
            )

        if manager_id is not None:
            statement = statement.where(
                Employee.manager_id == manager_id
            )

        if employment_status is not None:
            statement = statement.where(
                Employee.employment_status == employment_status
            )

        if not include_inactive:
            statement = statement.where(
                Employee.is_active.is_(True)
            )

        if search is not None:
            normalized = search.strip().lower()

            if normalized:
                pattern = f"%{normalized}%"

                statement = statement.where(
                    or_(
                        func.lower(Employee.employee_code).like(pattern),
                        func.lower(Employee.first_name).like(pattern),
                        func.lower(Employee.last_name).like(pattern),
                        func.lower(Employee.work_email).like(pattern),
                        func.lower(Employee.job_title).like(pattern),
                    )
                )

        statement = statement.order_by(
            Employee.first_name.asc(),
            Employee.last_name.asc(),
            Employee.created_at.asc(),
        )

        result = await self.session.execute(statement)
        return result.scalars().all()


__all__ = ["ScopedEmployeeRepository"]