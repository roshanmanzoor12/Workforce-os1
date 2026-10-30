from __future__ import annotations

import os
import uuid

import httpx
import pytest
from sqlalchemy import delete, select

from app.db.tenant import (
    dispose_all_tenant_engines,
    tenant_session,
)
from app.db.tenant_dependency import get_tenant_scope
from app.main import app
from app.modules.employees.models import (
    Department,
    Employee,
    Team,
)


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
        "for employee API integration tests."
    ),
)


# =========================================================
# TEST IDENTITIES
# =========================================================

WORKSPACE_ID = uuid.UUID(
    "34527ffb-e094-4e5e-89ee-4cab97244fc3"
)

TEST_SUFFIX = uuid.uuid4().hex[:8]

DEPARTMENT_NAME = (
    f"API Engineering {TEST_SUFFIX}"
)

DEPARTMENT_CODE = (
    f"API-D-{TEST_SUFFIX}"
)

TEAM_NAME = (
    f"API Platform {TEST_SUFFIX}"
)

TEAM_CODE = (
    f"API-T-{TEST_SUFFIX}"
)

MANAGER_CODE = (
    f"API-M-{TEST_SUFFIX}"
)

EMPLOYEE_CODE = (
    f"API-E-{TEST_SUFFIX}"
)

MANAGER_EMAIL = (
    f"api-manager-{TEST_SUFFIX}@example.com"
)

EMPLOYEE_EMAIL = (
    f"api-employee-{TEST_SUFFIX}@example.com"
)


# =========================================================
# CLEANUP
# =========================================================


async def cleanup_records(
    session,
) -> None:
    """
    Delete only rows created by this API integration test.

    Employees must be removed before teams and departments
    because of tenant-local foreign-key relationships.
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
# REAL TENANT SCOPE OVERRIDE
# =========================================================


class IntegrationTenantScope:
    """
    Minimal tenant scope used only for API integration tests.

    Authentication and tenant authorization have dedicated tests.

    This scope preserves the trusted role contract required by
    organization RBAC while still exercising:

        HTTP
        -> employee router
        -> RBAC
        -> service
        -> repository
        -> physical tenant PostgreSQL
    """

    def __init__(
        self,
        session,
        *,
        role_key: str = "owner",
    ) -> None:
        self.session = session
        self.workspace_id = WORKSPACE_ID
        self.role_key = role_key


# =========================================================
# MAIN REAL TENANT API FLOW
# =========================================================


@pytest.mark.asyncio
async def test_employee_api_real_tenant_flow(
) -> None:
    assert TENANT_DATABASE_NAME is not None

    async with tenant_session(
        TENANT_DATABASE_NAME
    ) as session:
        await cleanup_records(
            session
        )

        async def override_tenant_scope():
            return IntegrationTenantScope(
                session,
                role_key="owner",
            )

        app.dependency_overrides[
            get_tenant_scope
        ] = override_tenant_scope

        transport = httpx.ASGITransport(
            app=app
        )

        try:
            async with httpx.AsyncClient(
                transport=transport,
                base_url="http://testserver",
            ) as client:

                # =========================================
                # CREATE DEPARTMENT
                # =========================================

                response = await client.post(
                    (
                        f"/api/v1/workspaces/"
                        f"{WORKSPACE_ID}/departments"
                    ),
                    json={
                        "name": DEPARTMENT_NAME,
                        "code": DEPARTMENT_CODE,
                        "description": (
                            "API integration department"
                        ),
                    },
                )

                assert (
                    response.status_code
                    == 201
                ), response.text

                department = (
                    response.json()[
                        "department"
                    ]
                )

                department_id = (
                    department["id"]
                )

                assert (
                    department["name"]
                    == DEPARTMENT_NAME
                )

                assert (
                    department["code"]
                    == DEPARTMENT_CODE
                )

                assert (
                    department["is_active"]
                    is True
                )

                # =========================================
                # GET DEPARTMENT
                # =========================================

                response = await client.get(
                    (
                        f"/api/v1/workspaces/"
                        f"{WORKSPACE_ID}"
                        f"/departments/"
                        f"{department_id}"
                    )
                )

                assert (
                    response.status_code
                    == 200
                ), response.text

                assert (
                    response.json()[
                        "department"
                    ]["id"]
                    == department_id
                )

                # =========================================
                # CREATE TEAM
                # =========================================

                response = await client.post(
                    (
                        f"/api/v1/workspaces/"
                        f"{WORKSPACE_ID}/teams"
                    ),
                    json={
                        "name": TEAM_NAME,
                        "code": TEAM_CODE,
                        "description": (
                            "API integration team"
                        ),
                        "department_id": (
                            department_id
                        ),
                    },
                )

                assert (
                    response.status_code
                    == 201
                ), response.text

                team = (
                    response.json()[
                        "team"
                    ]
                )

                team_id = (
                    team["id"]
                )

                assert (
                    team["name"]
                    == TEAM_NAME
                )

                assert (
                    team["department_id"]
                    == department_id
                )

                # =========================================
                # CREATE MANAGER
                # =========================================

                response = await client.post(
                    (
                        f"/api/v1/workspaces/"
                        f"{WORKSPACE_ID}/employees"
                    ),
                    json={
                        "employee_code": (
                            MANAGER_CODE
                        ),
                        "first_name": "API",
                        "last_name": "Manager",
                        "work_email": (
                            MANAGER_EMAIL
                        ),
                        "job_title": (
                            "Engineering Manager"
                        ),
                        "employment_status": (
                            "active"
                        ),
                        "hire_date": (
                            "2026-01-01"
                        ),
                        "department_id": (
                            department_id
                        ),
                        "team_id": team_id,
                    },
                )

                assert (
                    response.status_code
                    == 201
                ), response.text

                manager = (
                    response.json()[
                        "employee"
                    ]
                )

                manager_id = (
                    manager["id"]
                )

                assert (
                    manager["employee_code"]
                    == MANAGER_CODE
                )

                assert (
                    manager["manager_id"]
                    is None
                )

                # =========================================
                # CREATE EMPLOYEE
                # =========================================

                response = await client.post(
                    (
                        f"/api/v1/workspaces/"
                        f"{WORKSPACE_ID}/employees"
                    ),
                    json={
                        "employee_code": (
                            EMPLOYEE_CODE
                        ),
                        "first_name": "API",
                        "last_name": "Employee",
                        "work_email": (
                            EMPLOYEE_EMAIL
                        ),
                        "job_title": (
                            "Software Engineer"
                        ),
                        "employment_status": (
                            "active"
                        ),
                        "hire_date": (
                            "2026-02-01"
                        ),
                        "department_id": (
                            department_id
                        ),
                        "team_id": team_id,
                        "manager_id": (
                            manager_id
                        ),
                    },
                )

                assert (
                    response.status_code
                    == 201
                ), response.text

                employee = (
                    response.json()[
                        "employee"
                    ]
                )

                employee_id = (
                    employee["id"]
                )

                assert (
                    employee["employee_code"]
                    == EMPLOYEE_CODE
                )

                assert (
                    employee["department_id"]
                    == department_id
                )

                assert (
                    employee["team_id"]
                    == team_id
                )

                assert (
                    employee["manager_id"]
                    == manager_id
                )

                # =========================================
                # GET EMPLOYEE DETAIL
                # =========================================

                response = await client.get(
                    (
                        f"/api/v1/workspaces/"
                        f"{WORKSPACE_ID}"
                        f"/employees/"
                        f"{employee_id}"
                    )
                )

                assert (
                    response.status_code
                    == 200
                ), response.text

                detail = response.json()

                assert (
                    detail["employee"]["id"]
                    == employee_id
                )

                assert (
                    detail["department"]["id"]
                    == department_id
                )

                assert (
                    detail["team"]["id"]
                    == team_id
                )

                assert (
                    detail["manager"]["id"]
                    == manager_id
                )

                # =========================================
                # LIST EMPLOYEES
                # =========================================

                response = await client.get(
                    (
                        f"/api/v1/workspaces/"
                        f"{WORKSPACE_ID}/employees"
                    ),
                    params={
                        "department_id": (
                            department_id
                        ),
                        "team_id": team_id,
                    },
                )

                assert (
                    response.status_code
                    == 200
                ), response.text

                body = response.json()

                ids = {
                    item["id"]
                    for item
                    in body["employees"]
                }

                assert manager_id in ids
                assert employee_id in ids

                # =========================================
                # SEARCH EMPLOYEE
                # =========================================

                response = await client.get(
                    (
                        f"/api/v1/workspaces/"
                        f"{WORKSPACE_ID}/employees"
                    ),
                    params={
                        "search": EMPLOYEE_CODE,
                    },
                )

                assert (
                    response.status_code
                    == 200
                ), response.text

                body = response.json()

                assert body["total"] >= 1

                assert any(
                    item[
                        "employee_code"
                    ]
                    == EMPLOYEE_CODE
                    for item
                    in body["employees"]
                )

                # =========================================
                # UPDATE EMPLOYEE
                # =========================================

                response = await client.patch(
                    (
                        f"/api/v1/workspaces/"
                        f"{WORKSPACE_ID}"
                        f"/employees/"
                        f"{employee_id}"
                    ),
                    json={
                        "job_title": (
                            "Senior Software Engineer"
                        )
                    },
                )

                assert (
                    response.status_code
                    == 200
                ), response.text

                updated_employee = (
                    response.json()[
                        "employee"
                    ]
                )

                assert (
                    updated_employee[
                        "job_title"
                    ]
                    == "Senior Software Engineer"
                )

                # =========================================
                # VERIFY PHYSICAL POSTGRES RECORD
                # =========================================

                result = await session.execute(
                    select(
                        Employee
                    ).where(
                        Employee.id
                        == uuid.UUID(
                            employee_id
                        )
                    )
                )

                persisted_employee = (
                    result.scalar_one()
                )

                assert (
                    persisted_employee.employee_code
                    == EMPLOYEE_CODE
                )

                assert (
                    persisted_employee.job_title
                    == "Senior Software Engineer"
                )

                assert (
                    str(
                        persisted_employee.department_id
                    )
                    == department_id
                )

                assert (
                    str(
                        persisted_employee.team_id
                    )
                    == team_id
                )

                assert (
                    str(
                        persisted_employee.manager_id
                    )
                    == manager_id
                )

                # =========================================
                # DEACTIVATE EMPLOYEE
                # =========================================

                response = await client.delete(
                    (
                        f"/api/v1/workspaces/"
                        f"{WORKSPACE_ID}"
                        f"/employees/"
                        f"{employee_id}"
                    )
                )

                assert (
                    response.status_code
                    == 200
                ), response.text

                assert (
                    response.json()[
                        "success"
                    ]
                    is True
                )

                # =========================================
                # DEFAULT LIST EXCLUDES INACTIVE
                # =========================================

                response = await client.get(
                    (
                        f"/api/v1/workspaces/"
                        f"{WORKSPACE_ID}/employees"
                    ),
                    params={
                        "search": EMPLOYEE_CODE,
                    },
                )

                assert (
                    response.status_code
                    == 200
                ), response.text

                body = response.json()

                assert all(
                    item[
                        "employee_code"
                    ]
                    != EMPLOYEE_CODE
                    for item
                    in body["employees"]
                )

                # =========================================
                # INCLUDE INACTIVE RETURNS EMPLOYEE
                # =========================================

                response = await client.get(
                    (
                        f"/api/v1/workspaces/"
                        f"{WORKSPACE_ID}/employees"
                    ),
                    params={
                        "search": EMPLOYEE_CODE,
                        "include_inactive": "true",
                    },
                )

                assert (
                    response.status_code
                    == 200
                ), response.text

                body = response.json()

                assert any(
                    (
                        item[
                            "employee_code"
                        ]
                        == EMPLOYEE_CODE
                        and item[
                            "is_active"
                        ]
                        is False
                    )
                    for item
                    in body["employees"]
                )

        finally:
            app.dependency_overrides.pop(
                get_tenant_scope,
                None,
            )

            await cleanup_records(
                session
            )

    await dispose_all_tenant_engines()


# =========================================================
# MEMBER RBAC HTTP CONTRACT
# =========================================================


@pytest.mark.asyncio
async def test_member_can_read_but_cannot_write(
) -> None:
    assert TENANT_DATABASE_NAME is not None

    async with tenant_session(
        TENANT_DATABASE_NAME
    ) as session:

        async def override_member_scope():
            return IntegrationTenantScope(
                session,
                role_key="member",
            )

        app.dependency_overrides[
            get_tenant_scope
        ] = override_member_scope

        transport = httpx.ASGITransport(
            app=app
        )

        try:
            async with httpx.AsyncClient(
                transport=transport,
                base_url="http://testserver",
            ) as client:

                # Member may read organization data.

                response = await client.get(
                    (
                        f"/api/v1/workspaces/"
                        f"{WORKSPACE_ID}/departments"
                    )
                )

                assert (
                    response.status_code
                    == 200
                ), response.text

                # Member may not create organization data.

                response = await client.post(
                    (
                        f"/api/v1/workspaces/"
                        f"{WORKSPACE_ID}/departments"
                    ),
                    json={
                        "name": (
                            f"Forbidden Department "
                            f"{TEST_SUFFIX}"
                        ),
                        "code": (
                            f"NO-{TEST_SUFFIX}"
                        ),
                    },
                )

                assert (
                    response.status_code
                    == 422
                ), response.text

                body = response.json()

                assert (
                    body["error"]["code"]
                    == "VALIDATION_ERROR"
                )

                assert (
                    "Owner or admin"
                    in body["error"]["message"]
                )

        finally:
            app.dependency_overrides.pop(
                get_tenant_scope,
                None,
            )

    await dispose_all_tenant_engines()


# =========================================================
# INVALID REQUEST CONTRACT
# =========================================================


@pytest.mark.asyncio
async def test_employee_api_rejects_invalid_payload(
) -> None:
    assert TENANT_DATABASE_NAME is not None

    async with tenant_session(
        TENANT_DATABASE_NAME
    ) as session:

        async def override_tenant_scope():
            return IntegrationTenantScope(
                session,
                role_key="owner",
            )

        app.dependency_overrides[
            get_tenant_scope
        ] = override_tenant_scope

        transport = httpx.ASGITransport(
            app=app
        )

        try:
            async with httpx.AsyncClient(
                transport=transport,
                base_url="http://testserver",
            ) as client:
                response = await client.post(
                    (
                        f"/api/v1/workspaces/"
                        f"{WORKSPACE_ID}/employees"
                    ),
                    json={
                        "employee_code": "",
                        "first_name": "",
                        "last_name": "",
                    },
                )

                assert (
                    response.status_code
                    == 422
                )

        finally:
            app.dependency_overrides.pop(
                get_tenant_scope,
                None,
            )

    await dispose_all_tenant_engines()