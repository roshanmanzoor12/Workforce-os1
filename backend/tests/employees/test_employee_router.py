from __future__ import annotations

import inspect
import uuid
from datetime import date, datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.routing import APIRoute

from app.core.exceptions import ValidationError
from app.db.tenant_dependency import get_tenant_scope
from app.main import app
from app.modules.employees.router import (
    EMPLOYEE_WRITE_ROLES,
    create_department,
    create_employee,
    create_team,
    delete_department,
    delete_employee,
    delete_team,
    get_department,
    get_employee,
    get_scope_role,
    get_team,
    list_departments,
    list_employees,
    list_teams,
    require_employee_write_access,
    router as employees_router,
    update_department,
    update_employee,
    update_team,
)
from app.modules.employees.schemas import (
    DepartmentCreateRequest,
    DepartmentDeleteResponse,
    DepartmentListResponse,
    DepartmentPublic,
    DepartmentResponse,
    EmployeeCreateRequest,
    EmployeeDeleteResponse,
    EmployeeDetailResponse,
    EmployeeListResponse,
    EmployeePublic,
    EmployeeResponse,
    EmployeeUpdateRequest,
    TeamCreateRequest,
    TeamDeleteResponse,
    TeamListResponse,
    TeamPublic,
    TeamResponse,
)


# =========================================================
# CONSTANTS
# =========================================================

WORKSPACE_ID = uuid.UUID(
    "11111111-1111-4111-8111-111111111111"
)

DEPARTMENT_ID = uuid.UUID(
    "22222222-2222-4222-8222-222222222222"
)

TEAM_ID = uuid.UUID(
    "33333333-3333-4333-8333-333333333333"
)

EMPLOYEE_ID = uuid.UUID(
    "44444444-4444-4444-8444-444444444444"
)

ROUTER_PREFIX = (
    "/workspaces/{workspace_id}"
)

OPENAPI_PREFIX = (
    "/api/v1/workspaces/{workspace_id}"
)


# =========================================================
# HELPERS
# =========================================================


def get_employee_api_route(
    *,
    path: str,
    method: str,
) -> APIRoute:
    for route in employees_router.routes:
        if not isinstance(
            route,
            APIRoute,
        ):
            continue

        if route.path != path:
            continue

        if method.upper() not in route.methods:
            continue

        return route

    raise AssertionError(
        f"Employee route not found: {method} {path}"
    )


def dependency_contains_call(
    dependency,
    target,
) -> bool:
    if dependency.call is target:
        return True

    return any(
        dependency_contains_call(
            child,
            target,
        )
        for child in dependency.dependencies
    )


def make_scope(
    *,
    role_key: str = "owner",
):
    return SimpleNamespace(
        session=AsyncMock(),
        workspace_id=WORKSPACE_ID,
        role_key=role_key,
    )


def make_context_scope(
    *,
    role_key: str,
):
    return SimpleNamespace(
        session=AsyncMock(),
        workspace_id=WORKSPACE_ID,
        context=SimpleNamespace(
            role_key=role_key,
        ),
    )


def make_department_public() -> DepartmentPublic:
    now = datetime.now(
        timezone.utc
    )

    return DepartmentPublic(
        id=DEPARTMENT_ID,
        name="Engineering",
        code="ENG",
        description=None,
        is_active=True,
        created_at=now,
        updated_at=now,
    )


def make_team_public() -> TeamPublic:
    now = datetime.now(
        timezone.utc
    )

    return TeamPublic(
        id=TEAM_ID,
        name="Platform",
        code="PLAT",
        description=None,
        department_id=DEPARTMENT_ID,
        is_active=True,
        created_at=now,
        updated_at=now,
    )


def make_employee_public() -> EmployeePublic:
    now = datetime.now(
        timezone.utc
    )

    return EmployeePublic(
        id=EMPLOYEE_ID,
        user_id=None,
        employee_code="EMP-001",
        first_name="Alice",
        last_name="Smith",
        full_name="Alice Smith",
        work_email="alice@example.com",
        phone_number=None,
        avatar_url=None,
        job_title="Engineer",
        employment_status="active",
        hire_date=date(
            2026,
            1,
            1,
        ),
        termination_date=None,
        department_id=DEPARTMENT_ID,
        team_id=TEAM_ID,
        manager_id=None,
        is_active=True,
        created_at=now,
        updated_at=now,
    )


# =========================================================
# ROUTE COUNT
# =========================================================


def test_employee_router_has_expected_route_count(
) -> None:
    routes = [
        route
        for route in employees_router.routes
        if isinstance(
            route,
            APIRoute,
        )
    ]

    assert len(routes) == 15


# =========================================================
# ROUTE REGISTRATION
# =========================================================


@pytest.mark.parametrize(
    (
        "method",
        "router_path",
        "openapi_path",
    ),
    [
        (
            "POST",
            f"{ROUTER_PREFIX}/departments",
            f"{OPENAPI_PREFIX}/departments",
        ),
        (
            "GET",
            f"{ROUTER_PREFIX}/departments",
            f"{OPENAPI_PREFIX}/departments",
        ),
        (
            "GET",
            (
                f"{ROUTER_PREFIX}"
                "/departments/{department_id}"
            ),
            (
                f"{OPENAPI_PREFIX}"
                "/departments/{department_id}"
            ),
        ),
        (
            "PATCH",
            (
                f"{ROUTER_PREFIX}"
                "/departments/{department_id}"
            ),
            (
                f"{OPENAPI_PREFIX}"
                "/departments/{department_id}"
            ),
        ),
        (
            "DELETE",
            (
                f"{ROUTER_PREFIX}"
                "/departments/{department_id}"
            ),
            (
                f"{OPENAPI_PREFIX}"
                "/departments/{department_id}"
            ),
        ),
        (
            "POST",
            f"{ROUTER_PREFIX}/teams",
            f"{OPENAPI_PREFIX}/teams",
        ),
        (
            "GET",
            f"{ROUTER_PREFIX}/teams",
            f"{OPENAPI_PREFIX}/teams",
        ),
        (
            "GET",
            (
                f"{ROUTER_PREFIX}"
                "/teams/{team_id}"
            ),
            (
                f"{OPENAPI_PREFIX}"
                "/teams/{team_id}"
            ),
        ),
        (
            "PATCH",
            (
                f"{ROUTER_PREFIX}"
                "/teams/{team_id}"
            ),
            (
                f"{OPENAPI_PREFIX}"
                "/teams/{team_id}"
            ),
        ),
        (
            "DELETE",
            (
                f"{ROUTER_PREFIX}"
                "/teams/{team_id}"
            ),
            (
                f"{OPENAPI_PREFIX}"
                "/teams/{team_id}"
            ),
        ),
        (
            "POST",
            f"{ROUTER_PREFIX}/employees",
            f"{OPENAPI_PREFIX}/employees",
        ),
        (
            "GET",
            f"{ROUTER_PREFIX}/employees",
            f"{OPENAPI_PREFIX}/employees",
        ),
        (
            "GET",
            (
                f"{ROUTER_PREFIX}"
                "/employees/{employee_id}"
            ),
            (
                f"{OPENAPI_PREFIX}"
                "/employees/{employee_id}"
            ),
        ),
        (
            "PATCH",
            (
                f"{ROUTER_PREFIX}"
                "/employees/{employee_id}"
            ),
            (
                f"{OPENAPI_PREFIX}"
                "/employees/{employee_id}"
            ),
        ),
        (
            "DELETE",
            (
                f"{ROUTER_PREFIX}"
                "/employees/{employee_id}"
            ),
            (
                f"{OPENAPI_PREFIX}"
                "/employees/{employee_id}"
            ),
        ),
    ],
)
def test_employee_routes_registered(
    method: str,
    router_path: str,
    openapi_path: str,
) -> None:
    route = get_employee_api_route(
        path=router_path,
        method=method,
    )

    assert route is not None
    assert openapi_path in app.openapi()["paths"]


# =========================================================
# TENANT SECURITY DEPENDENCY
# =========================================================


@pytest.mark.parametrize(
    (
        "method",
        "path",
    ),
    [
        (
            "POST",
            f"{ROUTER_PREFIX}/departments",
        ),
        (
            "GET",
            f"{ROUTER_PREFIX}/departments",
        ),
        (
            "POST",
            f"{ROUTER_PREFIX}/teams",
        ),
        (
            "GET",
            f"{ROUTER_PREFIX}/teams",
        ),
        (
            "POST",
            f"{ROUTER_PREFIX}/employees",
        ),
        (
            "GET",
            f"{ROUTER_PREFIX}/employees",
        ),
    ],
)
def test_employee_routes_require_tenant_scope(
    method: str,
    path: str,
) -> None:
    route = get_employee_api_route(
        path=path,
        method=method,
    )

    assert dependency_contains_call(
        route.dependant,
        get_tenant_scope,
    )


# =========================================================
# NO CLIENT DATABASE SELECTION
# =========================================================


@pytest.mark.parametrize(
    "handler",
    [
        create_department,
        list_departments,
        get_department,
        update_department,
        delete_department,
        create_team,
        list_teams,
        get_team,
        update_team,
        delete_team,
        create_employee,
        list_employees,
        get_employee,
        update_employee,
        delete_employee,
    ],
)
def test_employee_handlers_do_not_accept_database_identity(
    handler,
) -> None:
    parameters = set(
        inspect.signature(
            handler
        ).parameters
    )

    assert "database_name" not in parameters
    assert "database_url" not in parameters
    assert "cluster_key" not in parameters


# =========================================================
# RBAC
# =========================================================


def test_employee_write_roles_are_owner_and_admin(
) -> None:
    assert EMPLOYEE_WRITE_ROLES == frozenset(
        {
            "owner",
            "admin",
        }
    )


def test_get_scope_role_from_direct_scope(
) -> None:
    scope = make_scope(
        role_key="owner"
    )

    assert get_scope_role(
        scope
    ) == "owner"


def test_get_scope_role_from_context(
) -> None:
    scope = make_context_scope(
        role_key="admin"
    )

    assert get_scope_role(
        scope
    ) == "admin"


def test_get_scope_role_returns_none_without_role(
) -> None:
    scope = SimpleNamespace(
        session=AsyncMock(),
        workspace_id=WORKSPACE_ID,
    )

    assert get_scope_role(
        scope
    ) is None


@pytest.mark.parametrize(
    "role_key",
    [
        "owner",
        "admin",
    ],
)
def test_owner_and_admin_have_write_access(
    role_key: str,
) -> None:
    scope = make_scope(
        role_key=role_key
    )

    require_employee_write_access(
        scope
    )


@pytest.mark.parametrize(
    "role_key",
    [
        "member",
        "viewer",
        "",
    ],
)
def test_non_admin_roles_cannot_write(
    role_key: str,
) -> None:
    scope = make_scope(
        role_key=role_key
    )

    with pytest.raises(
        ValidationError,
        match="Owner or admin",
    ):
        require_employee_write_access(
            scope
        )


def test_missing_role_cannot_write(
) -> None:
    scope = SimpleNamespace(
        session=AsyncMock(),
        workspace_id=WORKSPACE_ID,
    )

    with pytest.raises(
        ValidationError,
        match="Owner or admin",
    ):
        require_employee_write_access(
            scope
        )


# =========================================================
# DEPARTMENT HANDLERS
# =========================================================


@pytest.mark.asyncio
async def test_create_department_calls_service(
) -> None:
    scope = make_scope(
        role_key="owner"
    )

    payload = DepartmentCreateRequest(
        name="Engineering",
        code="ENG",
    )

    expected = DepartmentResponse(
        message="Department created.",
        department=make_department_public(),
    )

    service = SimpleNamespace(
        create_department=AsyncMock(
            return_value=expected
        )
    )

    with patch(
        "app.modules.employees.router.get_employee_service",
        return_value=service,
    ):
        response = await create_department(
            payload=payload,
            scope=scope,
        )

    service.create_department.assert_awaited_once_with(
        payload
    )

    assert response == expected


@pytest.mark.asyncio
async def test_member_cannot_create_department(
) -> None:
    scope = make_scope(
        role_key="member"
    )

    payload = DepartmentCreateRequest(
        name="Engineering",
        code="ENG",
    )

    with pytest.raises(
        ValidationError,
        match="Owner or admin",
    ):
        await create_department(
            payload=payload,
            scope=scope,
        )


@pytest.mark.asyncio
async def test_list_departments_calls_service(
) -> None:
    scope = make_scope(
        role_key="member"
    )

    expected = DepartmentListResponse(
        departments=[
            make_department_public()
        ],
        total=1,
    )

    service = SimpleNamespace(
        list_departments=AsyncMock(
            return_value=expected
        )
    )

    with patch(
        "app.modules.employees.router.get_employee_service",
        return_value=service,
    ):
        response = await list_departments(
            scope=scope,
            include_inactive=False,
        )

    service.list_departments.assert_awaited_once_with(
        include_inactive=False,
    )

    assert response.total == 1


# =========================================================
# TEAM HANDLERS
# =========================================================


@pytest.mark.asyncio
async def test_create_team_calls_service(
) -> None:
    scope = make_scope(
        role_key="admin"
    )

    payload = TeamCreateRequest(
        name="Platform",
        code="PLAT",
        department_id=DEPARTMENT_ID,
    )

    expected = TeamResponse(
        message="Team created.",
        team=make_team_public(),
    )

    service = SimpleNamespace(
        create_team=AsyncMock(
            return_value=expected
        )
    )

    with patch(
        "app.modules.employees.router.get_employee_service",
        return_value=service,
    ):
        response = await create_team(
            payload=payload,
            scope=scope,
        )

    service.create_team.assert_awaited_once_with(
        payload
    )

    assert response == expected


@pytest.mark.asyncio
async def test_member_cannot_create_team(
) -> None:
    scope = make_scope(
        role_key="member"
    )

    payload = TeamCreateRequest(
        name="Platform",
        department_id=DEPARTMENT_ID,
    )

    with pytest.raises(
        ValidationError,
        match="Owner or admin",
    ):
        await create_team(
            payload=payload,
            scope=scope,
        )


@pytest.mark.asyncio
async def test_list_teams_calls_service(
) -> None:
    scope = make_scope(
        role_key="member"
    )

    expected = TeamListResponse(
        teams=[
            make_team_public()
        ],
        total=1,
    )

    service = SimpleNamespace(
        list_teams=AsyncMock(
            return_value=expected
        )
    )

    with patch(
        "app.modules.employees.router.get_employee_service",
        return_value=service,
    ):
        response = await list_teams(
            scope=scope,
            department_id=DEPARTMENT_ID,
            include_inactive=False,
        )

    service.list_teams.assert_awaited_once_with(
        department_id=DEPARTMENT_ID,
        include_inactive=False,
    )

    assert response.total == 1


# =========================================================
# EMPLOYEE HANDLERS
# =========================================================


@pytest.mark.asyncio
async def test_create_employee_calls_service(
) -> None:
    scope = make_scope(
        role_key="owner"
    )

    payload = EmployeeCreateRequest(
        employee_code="EMP-001",
        first_name="Alice",
        last_name="Smith",
        work_email="alice@example.com",
        department_id=DEPARTMENT_ID,
        team_id=TEAM_ID,
    )

    expected = EmployeeResponse(
        message="Employee created.",
        employee=make_employee_public(),
    )

    service = SimpleNamespace(
        create_employee=AsyncMock(
            return_value=expected
        )
    )

    with patch(
        "app.modules.employees.router.get_employee_service",
        return_value=service,
    ):
        response = await create_employee(
            payload=payload,
            scope=scope,
        )

    service.create_employee.assert_awaited_once_with(
        payload
    )

    assert response == expected


@pytest.mark.asyncio
async def test_member_cannot_create_employee(
) -> None:
    scope = make_scope(
        role_key="member"
    )

    payload = EmployeeCreateRequest(
        employee_code="EMP-001",
        first_name="Alice",
        last_name="Smith",
    )

    with pytest.raises(
        ValidationError,
        match="Owner or admin",
    ):
        await create_employee(
            payload=payload,
            scope=scope,
        )


@pytest.mark.asyncio
async def test_list_employees_calls_service(
) -> None:
    scope = make_scope(
        role_key="member"
    )

    expected = EmployeeListResponse(
        employees=[
            make_employee_public()
        ],
        total=1,
    )

    service = SimpleNamespace(
        list_employees=AsyncMock(
            return_value=expected
        )
    )

    with patch(
        "app.modules.employees.router.get_employee_service",
        return_value=service,
    ):
        response = await list_employees(
            scope=scope,
            department_id=DEPARTMENT_ID,
            team_id=TEAM_ID,
            manager_id=None,
            employment_status="active",
            include_inactive=False,
            search="Alice",
        )

    service.list_employees.assert_awaited_once_with(
        department_id=DEPARTMENT_ID,
        team_id=TEAM_ID,
        manager_id=None,
        employment_status="active",
        include_inactive=False,
        search="Alice",
    )

    assert response.total == 1


@pytest.mark.asyncio
async def test_get_employee_calls_service(
) -> None:
    scope = make_scope(
        role_key="member"
    )

    expected = EmployeeDetailResponse(
        employee=make_employee_public(),
        department=make_department_public(),
        team=make_team_public(),
        manager=None,
    )

    service = SimpleNamespace(
        get_employee=AsyncMock(
            return_value=expected
        )
    )

    with patch(
        "app.modules.employees.router.get_employee_service",
        return_value=service,
    ):
        response = await get_employee(
            employee_id=EMPLOYEE_ID,
            scope=scope,
        )

    service.get_employee.assert_awaited_once_with(
        employee_id=EMPLOYEE_ID,
    )

    assert response.employee.id == EMPLOYEE_ID


@pytest.mark.asyncio
async def test_update_employee_calls_service(
) -> None:
    scope = make_scope(
        role_key="admin"
    )

    payload = EmployeeUpdateRequest(
        job_title="Senior Engineer"
    )

    employee = make_employee_public().model_copy(
        update={
            "job_title": "Senior Engineer"
        }
    )

    expected = EmployeeResponse(
        message="Employee updated.",
        employee=employee,
    )

    service = SimpleNamespace(
        update_employee=AsyncMock(
            return_value=expected
        )
    )

    with patch(
        "app.modules.employees.router.get_employee_service",
        return_value=service,
    ):
        response = await update_employee(
            employee_id=EMPLOYEE_ID,
            payload=payload,
            scope=scope,
        )

    service.update_employee.assert_awaited_once_with(
        payload,
        employee_id=EMPLOYEE_ID,
    )

    assert (
        response.employee.job_title
        == "Senior Engineer"
    )


@pytest.mark.asyncio
async def test_member_cannot_update_employee(
) -> None:
    scope = make_scope(
        role_key="member"
    )

    payload = EmployeeUpdateRequest(
        job_title="Senior Engineer"
    )

    with pytest.raises(
        ValidationError,
        match="Owner or admin",
    ):
        await update_employee(
            employee_id=EMPLOYEE_ID,
            payload=payload,
            scope=scope,
        )


@pytest.mark.asyncio
async def test_delete_employee_calls_service(
) -> None:
    scope = make_scope(
        role_key="owner"
    )

    expected = EmployeeDeleteResponse(
        message="Employee deactivated.",
        success=True,
    )

    service = SimpleNamespace(
        delete_employee=AsyncMock(
            return_value=expected
        )
    )

    with patch(
        "app.modules.employees.router.get_employee_service",
        return_value=service,
    ):
        response = await delete_employee(
            employee_id=EMPLOYEE_ID,
            scope=scope,
        )

    service.delete_employee.assert_awaited_once_with(
        employee_id=EMPLOYEE_ID,
    )

    assert response.success is True


@pytest.mark.asyncio
async def test_member_cannot_delete_employee(
) -> None:
    scope = make_scope(
        role_key="member"
    )

    with pytest.raises(
        ValidationError,
        match="Owner or admin",
    ):
        await delete_employee(
            employee_id=EMPLOYEE_ID,
            scope=scope,
        )


# =========================================================
# DELETE RESPONSE CONTRACTS
# =========================================================


def test_department_delete_response_contract(
) -> None:
    response = DepartmentDeleteResponse(
        message="Department deactivated.",
        success=True,
    )

    assert response.success is True


def test_team_delete_response_contract(
) -> None:
    response = TeamDeleteResponse(
        message="Team deactivated.",
        success=True,
    )

    assert response.success is True