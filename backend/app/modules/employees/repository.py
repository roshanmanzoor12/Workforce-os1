from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.employees.models import (
    Department,
    Employee,
    Team,
)


# =========================================================
# EMPLOYEE REPOSITORY
# =========================================================


class EmployeeRepository:
    """
    Tenant-scoped repository for workforce organization data.

    Important:

    This repository must only receive an AsyncSession that was
    already resolved through the authorized tenant routing layer.

    It never selects or resolves a tenant database itself.
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    # =====================================================
    # DEPARTMENTS
    # =====================================================

    async def create_department(
        self,
        *,
        name: str,
        code: str | None = None,
        description: str | None = None,
        is_active: bool = True,
    ) -> Department:
        department = Department(
            name=name,
            code=code,
            description=description,
            is_active=is_active,
        )

        self.session.add(
            department
        )

        await self.session.flush()
        await self.session.refresh(
            department
        )

        return department

    async def get_department_by_id(
        self,
        department_id: uuid.UUID,
    ) -> Department | None:
        result = await self.session.execute(
            select(
                Department
            ).where(
                Department.id
                == department_id
            )
        )

        return result.scalar_one_or_none()

    async def list_departments(
        self,
        *,
        include_inactive: bool = False,
    ) -> Sequence[Department]:
        statement = select(
            Department
        )

        if not include_inactive:
            statement = statement.where(
                Department.is_active.is_(True)
            )

        statement = statement.order_by(
            Department.name.asc(),
            Department.created_at.asc(),
        )

        result = await self.session.execute(
            statement
        )

        return result.scalars().all()

    async def department_name_exists(
        self,
        name: str,
        *,
        exclude_id: uuid.UUID | None = None,
    ) -> bool:
        statement = select(
            func.count()
        ).select_from(
            Department
        ).where(
            func.lower(
                Department.name
            )
            == name.strip().lower()
        )

        if exclude_id is not None:
            statement = statement.where(
                Department.id
                != exclude_id
            )

        result = await self.session.execute(
            statement
        )

        return (
            result.scalar_one()
            > 0
        )

    async def department_code_exists(
        self,
        code: str,
        *,
        exclude_id: uuid.UUID | None = None,
    ) -> bool:
        statement = select(
            func.count()
        ).select_from(
            Department
        ).where(
            func.lower(
                Department.code
            )
            == code.strip().lower()
        )

        if exclude_id is not None:
            statement = statement.where(
                Department.id
                != exclude_id
            )

        result = await self.session.execute(
            statement
        )

        return (
            result.scalar_one()
            > 0
        )

    async def update_department(
        self,
        department: Department,
        *,
        values: dict[str, object],
    ) -> Department:
        for field_name, value in values.items():
            setattr(
                department,
                field_name,
                value,
            )

        self.session.add(
            department
        )

        await self.session.flush()
        await self.session.refresh(
            department
        )

        return department

    async def deactivate_department(
        self,
        department: Department,
    ) -> Department:
        department.is_active = False

        self.session.add(
            department
        )

        await self.session.flush()
        await self.session.refresh(
            department
        )

        return department

    # =====================================================
    # TEAMS
    # =====================================================

    async def create_team(
        self,
        *,
        name: str,
        code: str | None = None,
        description: str | None = None,
        department_id: uuid.UUID | None = None,
        is_active: bool = True,
    ) -> Team:
        team = Team(
            name=name,
            code=code,
            description=description,
            department_id=department_id,
            is_active=is_active,
        )

        self.session.add(
            team
        )

        await self.session.flush()
        await self.session.refresh(
            team
        )

        return team

    async def get_team_by_id(
        self,
        team_id: uuid.UUID,
    ) -> Team | None:
        result = await self.session.execute(
            select(
                Team
            )
            .options(
                selectinload(
                    Team.department
                )
            )
            .where(
                Team.id
                == team_id
            )
        )

        return result.scalar_one_or_none()

    async def list_teams(
        self,
        *,
        department_id: uuid.UUID | None = None,
        include_inactive: bool = False,
    ) -> Sequence[Team]:
        statement = (
            select(
                Team
            )
            .options(
                selectinload(
                    Team.department
                )
            )
        )

        if department_id is not None:
            statement = statement.where(
                Team.department_id
                == department_id
            )

        if not include_inactive:
            statement = statement.where(
                Team.is_active.is_(True)
            )

        statement = statement.order_by(
            Team.name.asc(),
            Team.created_at.asc(),
        )

        result = await self.session.execute(
            statement
        )

        return result.scalars().all()

    async def team_name_exists(
        self,
        *,
        name: str,
        department_id: uuid.UUID | None,
        exclude_id: uuid.UUID | None = None,
    ) -> bool:
        statement = select(
            func.count()
        ).select_from(
            Team
        ).where(
            func.lower(
                Team.name
            )
            == name.strip().lower()
        )

        if department_id is None:
            statement = statement.where(
                Team.department_id.is_(None)
            )
        else:
            statement = statement.where(
                Team.department_id
                == department_id
            )

        if exclude_id is not None:
            statement = statement.where(
                Team.id
                != exclude_id
            )

        result = await self.session.execute(
            statement
        )

        return (
            result.scalar_one()
            > 0
        )

    async def team_code_exists(
        self,
        code: str,
        *,
        exclude_id: uuid.UUID | None = None,
    ) -> bool:
        statement = select(
            func.count()
        ).select_from(
            Team
        ).where(
            func.lower(
                Team.code
            )
            == code.strip().lower()
        )

        if exclude_id is not None:
            statement = statement.where(
                Team.id
                != exclude_id
            )

        result = await self.session.execute(
            statement
        )

        return (
            result.scalar_one()
            > 0
        )

    async def update_team(
        self,
        team: Team,
        *,
        values: dict[str, object],
    ) -> Team:
        for field_name, value in values.items():
            setattr(
                team,
                field_name,
                value,
            )

        self.session.add(
            team
        )

        await self.session.flush()
        await self.session.refresh(
            team
        )

        return team

    async def deactivate_team(
        self,
        team: Team,
    ) -> Team:
        team.is_active = False

        self.session.add(
            team
        )

        await self.session.flush()
        await self.session.refresh(
            team
        )

        return team

    # =====================================================
    # EMPLOYEES
    # =====================================================

    async def create_employee(
        self,
        *,
        user_id: uuid.UUID | None,
        employee_code: str,
        first_name: str,
        last_name: str,
        work_email: str | None,
        phone_number: str | None,
        avatar_url: str | None,
        job_title: str | None,
        employment_status: str,
        hire_date,
        termination_date,
        department_id: uuid.UUID | None,
        team_id: uuid.UUID | None,
        manager_id: uuid.UUID | None,
        is_active: bool = True,
    ) -> Employee:
        employee = Employee(
            user_id=user_id,
            employee_code=employee_code,
            first_name=first_name,
            last_name=last_name,
            work_email=work_email,
            phone_number=phone_number,
            avatar_url=avatar_url,
            job_title=job_title,
            employment_status=employment_status,
            hire_date=hire_date,
            termination_date=termination_date,
            department_id=department_id,
            team_id=team_id,
            manager_id=manager_id,
            is_active=is_active,
        )

        self.session.add(
            employee
        )

        await self.session.flush()

        return employee

    async def get_employee_by_id(
        self,
        employee_id: uuid.UUID,
    ) -> Employee | None:
        result = await self.session.execute(
            select(
                Employee
            )
            .options(
                selectinload(
                    Employee.department
                ),
                selectinload(
                    Employee.team
                ),
                selectinload(
                    Employee.manager
                ),
            )
            .where(
                Employee.id
                == employee_id
            )
        )

        return result.scalar_one_or_none()

    async def get_employee_by_user_id(
        self,
        user_id: uuid.UUID,
    ) -> Employee | None:
        result = await self.session.execute(
            select(
                Employee
            ).where(
                Employee.user_id
                == user_id
            )
        )

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
    ) -> Sequence[Employee]:
        statement = (
            select(
                Employee
            )
            .options(
                selectinload(
                    Employee.department
                ),
                selectinload(
                    Employee.team
                ),
                selectinload(
                    Employee.manager
                ),
            )
        )

        if department_id is not None:
            statement = statement.where(
                Employee.department_id
                == department_id
            )

        if team_id is not None:
            statement = statement.where(
                Employee.team_id
                == team_id
            )

        if manager_id is not None:
            statement = statement.where(
                Employee.manager_id
                == manager_id
            )

        if employment_status is not None:
            statement = statement.where(
                Employee.employment_status
                == employment_status
            )

        if not include_inactive:
            statement = statement.where(
                Employee.is_active.is_(True)
            )

        if search is not None:
            normalized_search = (
                search
                .strip()
                .lower()
            )

            if normalized_search:
                pattern = (
                    f"%{normalized_search}%"
                )

                statement = statement.where(
                    or_(
                        func.lower(
                            Employee.employee_code
                        ).like(
                            pattern
                        ),
                        func.lower(
                            Employee.first_name
                        ).like(
                            pattern
                        ),
                        func.lower(
                            Employee.last_name
                        ).like(
                            pattern
                        ),
                        func.lower(
                            Employee.work_email
                        ).like(
                            pattern
                        ),
                        func.lower(
                            Employee.job_title
                        ).like(
                            pattern
                        ),
                    )
                )

        statement = statement.order_by(
            Employee.first_name.asc(),
            Employee.last_name.asc(),
            Employee.created_at.asc(),
        )

        result = await self.session.execute(
            statement
        )

        return result.scalars().all()

    async def employee_code_exists(
        self,
        employee_code: str,
        *,
        exclude_id: uuid.UUID | None = None,
    ) -> bool:
        statement = select(
            func.count()
        ).select_from(
            Employee
        ).where(
            func.lower(
                Employee.employee_code
            )
            == employee_code.strip().lower()
        )

        if exclude_id is not None:
            statement = statement.where(
                Employee.id
                != exclude_id
            )

        result = await self.session.execute(
            statement
        )

        return (
            result.scalar_one()
            > 0
        )

    async def employee_work_email_exists(
        self,
        work_email: str,
        *,
        exclude_id: uuid.UUID | None = None,
    ) -> bool:
        statement = select(
            func.count()
        ).select_from(
            Employee
        ).where(
            func.lower(
                Employee.work_email
            )
            == work_email.strip().lower()
        )

        if exclude_id is not None:
            statement = statement.where(
                Employee.id
                != exclude_id
            )

        result = await self.session.execute(
            statement
        )

        return (
            result.scalar_one()
            > 0
        )

    async def employee_user_id_exists(
        self,
        user_id: uuid.UUID,
        *,
        exclude_id: uuid.UUID | None = None,
    ) -> bool:
        statement = select(
            func.count()
        ).select_from(
            Employee
        ).where(
            Employee.user_id
            == user_id
        )

        if exclude_id is not None:
            statement = statement.where(
                Employee.id
                != exclude_id
            )

        result = await self.session.execute(
            statement
        )

        return (
            result.scalar_one()
            > 0
        )

    async def update_employee(
        self,
        employee: Employee,
        *,
        values: dict[str, object],
    ) -> Employee:
        for field_name, value in values.items():
            setattr(
                employee,
                field_name,
                value,
            )

        self.session.add(
            employee
        )

        await self.session.flush()

        return employee

    async def deactivate_employee(
        self,
        employee: Employee,
    ) -> Employee:
        employee.is_active = False

        self.session.add(
            employee
        )

        await self.session.flush()

        return employee

    # =====================================================
    # ORGANIZATION VALIDATION HELPERS
    # =====================================================

    async def employee_exists(
        self,
        employee_id: uuid.UUID,
    ) -> bool:
        result = await self.session.execute(
            select(
                func.count()
            )
            .select_from(
                Employee
            )
            .where(
                Employee.id
                == employee_id
            )
        )

        return (
            result.scalar_one()
            > 0
        )

    async def active_employee_exists(
        self,
        employee_id: uuid.UUID,
    ) -> bool:
        result = await self.session.execute(
            select(
                func.count()
            )
            .select_from(
                Employee
            )
            .where(
                Employee.id
                == employee_id,
                Employee.is_active.is_(
                    True
                ),
            )
        )

        return (
            result.scalar_one()
            > 0
        )

    async def department_exists(
        self,
        department_id: uuid.UUID,
    ) -> bool:
        result = await self.session.execute(
            select(
                func.count()
            )
            .select_from(
                Department
            )
            .where(
                Department.id
                == department_id
            )
        )

        return (
            result.scalar_one()
            > 0
        )

    async def active_department_exists(
        self,
        department_id: uuid.UUID,
    ) -> bool:
        result = await self.session.execute(
            select(
                func.count()
            )
            .select_from(
                Department
            )
            .where(
                Department.id
                == department_id,
                Department.is_active.is_(
                    True
                ),
            )
        )

        return (
            result.scalar_one()
            > 0
        )

    async def team_exists(
        self,
        team_id: uuid.UUID,
    ) -> bool:
        result = await self.session.execute(
            select(
                func.count()
            )
            .select_from(
                Team
            )
            .where(
                Team.id
                == team_id
            )
        )

        return (
            result.scalar_one()
            > 0
        )

    async def active_team_exists(
        self,
        team_id: uuid.UUID,
    ) -> bool:
        result = await self.session.execute(
            select(
                func.count()
            )
            .select_from(
                Team
            )
            .where(
                Team.id
                == team_id,
                Team.is_active.is_(
                    True
                ),
            )
        )

        return (
            result.scalar_one()
            > 0
        )

    async def team_belongs_to_department(
        self,
        *,
        team_id: uuid.UUID,
        department_id: uuid.UUID,
    ) -> bool:
        result = await self.session.execute(
            select(
                func.count()
            )
            .select_from(
                Team
            )
            .where(
                Team.id
                == team_id,
                Team.department_id
                == department_id,
            )
        )

        return (
            result.scalar_one()
            > 0
        )

    async def count_direct_reports(
        self,
        manager_id: uuid.UUID,
    ) -> int:
        result = await self.session.execute(
            select(
                func.count()
            )
            .select_from(
                Employee
            )
            .where(
                Employee.manager_id
                == manager_id
            )
        )

        return int(
            result.scalar_one()
        )


# =========================================================
# FACTORY
# =========================================================


def get_employee_repository(
    session: AsyncSession,
) -> EmployeeRepository:
    return EmployeeRepository(
        session
    )


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "EmployeeRepository",
    "get_employee_repository",
]