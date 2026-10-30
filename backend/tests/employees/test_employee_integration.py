from __future__ import annotations

import os
import uuid
from datetime import date

import pytest
from sqlalchemy import delete, select

from app.db.tenant import (
    dispose_all_tenant_engines,
    tenant_session,
)
from app.modules.employees.models import (
    Department,
    Employee,
    Team,
)
from app.modules.employees.schemas import (
    DepartmentCreateRequest,
    EmployeeCreateRequest,
    TeamCreateRequest,
)
from app.modules.employees.service import EmployeeService


# =========================================================
# INTEGRATION REQUIREMENTS
# =========================================================

TENANT_DATABASE_NAME = os.getenv(
    "TENANT_DB"
)

pytestmark = pytest.mark.skipif(
    not TENANT_DATABASE_NAME,
    reason=(
        "TENANT_DB environment variable is required "
        "for tenant integration tests."
    ),
)


# =========================================================
# TEST IDENTITIES
# =========================================================

TEST_SUFFIX = uuid.uuid4().hex[:8]

DEPARTMENT_CODE = (
    f"IT-{TEST_SUFFIX}"
)

TEAM_CODE = (
    f"TM-{TEST_SUFFIX}"
)

MANAGER_CODE = (
    f"MGR-{TEST_SUFFIX}"
)

EMPLOYEE_CODE = (
    f"EMP-{TEST_SUFFIX}"
)

MANAGER_EMAIL = (
    f"manager-{TEST_SUFFIX}@example.com"
)

EMPLOYEE_EMAIL = (
    f"employee-{TEST_SUFFIX}@example.com"
)


# =========================================================
# CLEANUP
# =========================================================


async def cleanup_test_records(
    session,
) -> None:
    """
    Remove only rows created by this integration test.

    Delete employees first because they reference teams,
    departments, and other employees.
    """

    await session.execute(
        delete(
            Employee
        ).where(
            Employee.employee_code.in_(
                [
                    MANAGER_CODE,
                    EMPLOYEE_CODE,
                ]
            )
        )
    )

    await session.execute(
        delete(
            Team
        ).where(
            Team.code
            == TEAM_CODE
        )
    )

    await session.execute(
        delete(
            Department
        ).where(
            Department.code
            == DEPARTMENT_CODE
        )
    )

    await session.commit()


# =========================================================
# REAL TENANT DATABASE FLOW
# =========================================================


@pytest.mark.asyncio
async def test_real_tenant_employee_organization_flow(
) -> None:
    assert TENANT_DATABASE_NAME is not None

    try:
        async with tenant_session(
            TENANT_DATABASE_NAME
        ) as session:
            await cleanup_test_records(
                session
            )

            service = EmployeeService(
                session
            )

            # =============================================
            # CREATE DEPARTMENT
            # =============================================

            department_response = (
                await service.create_department(
                    DepartmentCreateRequest(
                        name=(
                            f"Integration Engineering "
                            f"{TEST_SUFFIX}"
                        ),
                        code=DEPARTMENT_CODE,
                        description=(
                            "Employee integration test department"
                        ),
                    )
                )
            )

            department_id = (
                department_response.department.id
            )

            assert (
                department_response.department.code
                == DEPARTMENT_CODE
            )

            assert (
                department_response.department.is_active
                is True
            )

            # =============================================
            # CREATE TEAM
            # =============================================

            team_response = (
                await service.create_team(
                    TeamCreateRequest(
                        name=(
                            f"Integration Platform "
                            f"{TEST_SUFFIX}"
                        ),
                        code=TEAM_CODE,
                        description=(
                            "Employee integration test team"
                        ),
                        department_id=department_id,
                    )
                )
            )

            team_id = (
                team_response.team.id
            )

            assert (
                team_response.team.department_id
                == department_id
            )

            # =============================================
            # CREATE MANAGER
            # =============================================

            manager_response = (
                await service.create_employee(
                    EmployeeCreateRequest(
                        employee_code=MANAGER_CODE,
                        first_name="Integration",
                        last_name="Manager",
                        work_email=MANAGER_EMAIL,
                        job_title="Engineering Manager",
                        employment_status="active",
                        hire_date=date(
                            2026,
                            1,
                            1,
                        ),
                        department_id=department_id,
                        team_id=team_id,
                    )
                )
            )

            manager_id = (
                manager_response.employee.id
            )

            assert (
                manager_response.employee.employee_code
                == MANAGER_CODE
            )

            assert (
                manager_response.employee.manager_id
                is None
            )

            # =============================================
            # CREATE EMPLOYEE
            # =============================================

            employee_response = (
                await service.create_employee(
                    EmployeeCreateRequest(
                        employee_code=EMPLOYEE_CODE,
                        first_name="Integration",
                        last_name="Employee",
                        work_email=EMPLOYEE_EMAIL,
                        job_title="Software Engineer",
                        employment_status="active",
                        hire_date=date(
                            2026,
                            2,
                            1,
                        ),
                        department_id=department_id,
                        team_id=team_id,
                        manager_id=manager_id,
                    )
                )
            )

            employee_id = (
                employee_response.employee.id
            )

            assert (
                employee_response.employee.employee_code
                == EMPLOYEE_CODE
            )

            assert (
                employee_response.employee.department_id
                == department_id
            )

            assert (
                employee_response.employee.team_id
                == team_id
            )

            assert (
                employee_response.employee.manager_id
                == manager_id
            )

            # =============================================
            # READ EMPLOYEE DETAIL
            # =============================================

            detail = await service.get_employee(
                employee_id=employee_id
            )

            assert (
                detail.employee.id
                == employee_id
            )

            assert (
                detail.department
                is not None
            )

            assert (
                detail.department.id
                == department_id
            )

            assert (
                detail.team
                is not None
            )

            assert (
                detail.team.id
                == team_id
            )

            assert (
                detail.manager
                is not None
            )

            assert (
                detail.manager.id
                == manager_id
            )

            # =============================================
            # LIST EMPLOYEES
            # =============================================

            employee_list = (
                await service.list_employees(
                    department_id=department_id,
                    team_id=team_id,
                    include_inactive=False,
                )
            )

            employee_ids = {
                item.id
                for item in employee_list.employees
            }

            assert manager_id in employee_ids
            assert employee_id in employee_ids

            # =============================================
            # VERIFY PHYSICAL DB RECORDS
            # =============================================

            result = await session.execute(
                select(
                    Employee
                ).where(
                    Employee.employee_code.in_(
                        [
                            MANAGER_CODE,
                            EMPLOYEE_CODE,
                        ]
                    )
                )
            )

            physical_employees = (
                result.scalars().all()
            )

            assert len(
                physical_employees
            ) == 2

            result = await session.execute(
                select(
                    Department
                ).where(
                    Department.id
                    == department_id
                )
            )

            physical_department = (
                result.scalar_one()
            )

            assert (
                physical_department.code
                == DEPARTMENT_CODE
            )

            result = await session.execute(
                select(
                    Team
                ).where(
                    Team.id
                    == team_id
                )
            )

            physical_team = (
                result.scalar_one()
            )

            assert (
                physical_team.department_id
                == department_id
            )

            # =============================================
            # CLEANUP
            # =============================================

            await cleanup_test_records(
                session
            )

            # =============================================
            # VERIFY CLEANUP
            # =============================================

            result = await session.execute(
                select(
                    Employee
                ).where(
                    Employee.employee_code.in_(
                        [
                            MANAGER_CODE,
                            EMPLOYEE_CODE,
                        ]
                    )
                )
            )

            assert (
                result.scalars().all()
                == []
            )

    finally:
        await dispose_all_tenant_engines()