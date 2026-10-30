from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import (
    ConflictError,
    ResourceNotFound,
    ValidationError,
)
from app.modules.employees.models import (
    EMPLOYMENT_STATUS_ACTIVE,
    EMPLOYMENT_STATUS_TERMINATED,
)
from app.modules.employees.schemas import (
    DepartmentCreateRequest,
    DepartmentUpdateRequest,
    EmployeeCreateRequest,
    EmployeeUpdateRequest,
    TeamCreateRequest,
    TeamUpdateRequest,
)
from app.modules.employees.service import EmployeeService


# =========================================================
# CONSTANTS
# =========================================================

DEPARTMENT_ID = uuid.UUID(
    "11111111-1111-4111-8111-111111111111"
)

OTHER_DEPARTMENT_ID = uuid.UUID(
    "22222222-2222-4222-8222-222222222222"
)

TEAM_ID = uuid.UUID(
    "33333333-3333-4333-8333-333333333333"
)

EMPLOYEE_ID = uuid.UUID(
    "44444444-4444-4444-8444-444444444444"
)

MANAGER_ID = uuid.UUID(
    "55555555-5555-4555-8555-555555555555"
)

GLOBAL_USER_ID = uuid.UUID(
    "66666666-6666-4666-8666-666666666666"
)

TEST_TIMESTAMP = datetime(
    2026,
    8,
    21,
    12,
    0,
    0,
    tzinfo=timezone.utc,
)


# =========================================================
# HELPERS
# =========================================================


def make_department(
    *,
    department_id: uuid.UUID = DEPARTMENT_ID,
    name: str = "Engineering",
    code: str | None = "ENG",
    is_active: bool = True,
):
    return SimpleNamespace(
        id=department_id,
        name=name,
        code=code,
        description=None,
        is_active=is_active,
        created_at=TEST_TIMESTAMP,
        updated_at=TEST_TIMESTAMP,
    )


def make_team(
    *,
    team_id: uuid.UUID = TEAM_ID,
    department_id: uuid.UUID | None = DEPARTMENT_ID,
    name: str = "Platform",
    code: str | None = "PLAT",
    is_active: bool = True,
):
    return SimpleNamespace(
        id=team_id,
        name=name,
        code=code,
        description=None,
        department_id=department_id,
        is_active=is_active,
        created_at=TEST_TIMESTAMP,
        updated_at=TEST_TIMESTAMP,
    )


def make_employee(
    *,
    employee_id: uuid.UUID = EMPLOYEE_ID,
    user_id: uuid.UUID | None = None,
    employee_code: str = "EMP-001",
    first_name: str = "Alice",
    last_name: str = "Smith",
    work_email: str | None = "alice@example.com",
    department_id: uuid.UUID | None = DEPARTMENT_ID,
    team_id: uuid.UUID | None = TEAM_ID,
    manager_id: uuid.UUID | None = None,
    employment_status: str = EMPLOYMENT_STATUS_ACTIVE,
    hire_date: date | None = date(2026, 1, 1),
    termination_date: date | None = None,
    is_active: bool = True,
):
    return SimpleNamespace(
        id=employee_id,
        user_id=user_id,
        employee_code=employee_code,
        first_name=first_name,
        last_name=last_name,
        full_name=f"{first_name} {last_name}",
        work_email=work_email,
        phone_number=None,
        avatar_url=None,
        job_title="Engineer",
        employment_status=employment_status,
        hire_date=hire_date,
        termination_date=termination_date,
        department_id=department_id,
        team_id=team_id,
        manager_id=manager_id,
        is_active=is_active,
        department=None,
        team=None,
        manager=None,
        created_at=TEST_TIMESTAMP,
        updated_at=TEST_TIMESTAMP,
    )


def make_service():
    session = AsyncMock()

    service = EmployeeService(
        session
    )

    repository = AsyncMock()

    service.repository = repository

    return service, session, repository


# =========================================================
# DEPARTMENT TESTS
# =========================================================


@pytest.mark.asyncio
async def test_create_department_success() -> None:
    service, session, repository = make_service()

    repository.department_name_exists.return_value = False
    repository.department_code_exists.return_value = False

    department = make_department()

    repository.create_department.return_value = department

    request = DepartmentCreateRequest(
        name="Engineering",
        code="ENG",
    )

    response = await service.create_department(
        request
    )

    repository.create_department.assert_awaited_once_with(
        name="Engineering",
        code="ENG",
        description=None,
        is_active=True,
    )

    session.commit.assert_awaited_once()

    assert response.department.name == "Engineering"
    assert response.department.code == "ENG"


@pytest.mark.asyncio
async def test_create_department_duplicate_name_rejected() -> None:
    service, _, repository = make_service()

    repository.department_name_exists.return_value = True

    request = DepartmentCreateRequest(
        name="Engineering",
    )

    with pytest.raises(
        ConflictError
    ):
        await service.create_department(
            request
        )


@pytest.mark.asyncio
async def test_update_department_can_clear_code() -> None:
    service, session, repository = make_service()

    department = make_department()

    repository.get_department_by_id.return_value = department
    repository.update_department.return_value = department

    request = DepartmentUpdateRequest(
        code=None
    )

    await service.update_department(
        request,
        department_id=DEPARTMENT_ID,
    )

    repository.update_department.assert_awaited_once()

    values = (
        repository.update_department
        .await_args.kwargs["values"]
    )

    assert "code" in values
    assert values["code"] is None

    session.commit.assert_awaited_once()


# =========================================================
# TEAM TESTS
# =========================================================


@pytest.mark.asyncio
async def test_create_team_requires_active_department() -> None:
    service, _, repository = make_service()

    repository.get_department_by_id.return_value = (
        make_department(
            is_active=False
        )
    )

    request = TeamCreateRequest(
        name="Platform",
        department_id=DEPARTMENT_ID,
    )

    with pytest.raises(
        ValidationError,
        match="inactive",
    ):
        await service.create_team(
            request
        )


@pytest.mark.asyncio
async def test_create_team_duplicate_name_in_department_rejected() -> None:
    service, _, repository = make_service()

    repository.get_department_by_id.return_value = (
        make_department()
    )

    repository.team_name_exists.return_value = True

    request = TeamCreateRequest(
        name="Platform",
        department_id=DEPARTMENT_ID,
    )

    with pytest.raises(
        ConflictError
    ):
        await service.create_team(
            request
        )


@pytest.mark.asyncio
async def test_update_team_can_clear_department() -> None:
    service, session, repository = make_service()

    team = make_team()

    repository.get_team_by_id.return_value = team
    repository.team_name_exists.return_value = False
    repository.update_team.return_value = team

    request = TeamUpdateRequest(
        department_id=None
    )

    await service.update_team(
        request,
        team_id=TEAM_ID,
    )

    values = (
        repository.update_team
        .await_args.kwargs["values"]
    )

    assert "department_id" in values
    assert values["department_id"] is None

    session.commit.assert_awaited_once()


# =========================================================
# EMPLOYEE DUPLICATE TESTS
# =========================================================


@pytest.mark.asyncio
async def test_create_employee_duplicate_code_rejected() -> None:
    service, _, repository = make_service()

    repository.employee_code_exists.return_value = True

    request = EmployeeCreateRequest(
        employee_code="EMP-001",
        first_name="Alice",
        last_name="Smith",
    )

    with pytest.raises(
        ConflictError,
        match="Employee code",
    ):
        await service.create_employee(
            request
        )


@pytest.mark.asyncio
async def test_create_employee_duplicate_work_email_rejected() -> None:
    service, _, repository = make_service()

    repository.employee_code_exists.return_value = False
    repository.employee_work_email_exists.return_value = True

    request = EmployeeCreateRequest(
        employee_code="EMP-001",
        first_name="Alice",
        last_name="Smith",
        work_email="alice@example.com",
    )

    with pytest.raises(
        ConflictError,
        match="work email",
    ):
        await service.create_employee(
            request
        )


@pytest.mark.asyncio
async def test_create_employee_duplicate_global_user_link_rejected() -> None:
    service, _, repository = make_service()

    repository.employee_code_exists.return_value = False
    repository.employee_work_email_exists.return_value = False
    repository.employee_user_id_exists.return_value = True

    request = EmployeeCreateRequest(
        user_id=GLOBAL_USER_ID,
        employee_code="EMP-001",
        first_name="Alice",
        last_name="Smith",
    )

    with pytest.raises(
        ConflictError,
        match="global user",
    ):
        await service.create_employee(
            request
        )


# =========================================================
# ORGANIZATION CONSISTENCY
# =========================================================


@pytest.mark.asyncio
async def test_employee_team_must_match_department() -> None:
    service, _, repository = make_service()

    repository.employee_code_exists.return_value = False
    repository.employee_work_email_exists.return_value = False
    repository.employee_user_id_exists.return_value = False

    repository.get_department_by_id.return_value = (
        make_department()
    )

    repository.get_team_by_id.return_value = (
        make_team(
            department_id=OTHER_DEPARTMENT_ID
        )
    )

    request = EmployeeCreateRequest(
        employee_code="EMP-001",
        first_name="Alice",
        last_name="Smith",
        department_id=DEPARTMENT_ID,
        team_id=TEAM_ID,
    )

    with pytest.raises(
        ValidationError,
        match="Team does not belong",
    ):
        await service.create_employee(
            request
        )


@pytest.mark.asyncio
async def test_employee_cannot_select_departmentless_value_with_department_team() -> None:
    service, _, repository = make_service()

    repository.employee_code_exists.return_value = False
    repository.employee_work_email_exists.return_value = False
    repository.employee_user_id_exists.return_value = False

    repository.get_team_by_id.return_value = (
        make_team(
            department_id=DEPARTMENT_ID
        )
    )

    request = EmployeeCreateRequest(
        employee_code="EMP-001",
        first_name="Alice",
        last_name="Smith",
        department_id=None,
        team_id=TEAM_ID,
    )

    with pytest.raises(
        ValidationError,
        match="department must match",
    ):
        await service.create_employee(
            request
        )


# =========================================================
# MANAGER RULES
# =========================================================


@pytest.mark.asyncio
async def test_employee_cannot_be_own_manager() -> None:
    service, _, repository = make_service()

    employee = make_employee()

    repository.get_employee_by_id.return_value = employee

    request = EmployeeUpdateRequest(
        manager_id=EMPLOYEE_ID
    )

    with pytest.raises(
        ValidationError,
        match="own manager",
    ):
        await service.update_employee(
            request,
            employee_id=EMPLOYEE_ID,
        )


@pytest.mark.asyncio
async def test_inactive_employee_cannot_be_manager() -> None:
    service, _, repository = make_service()

    employee = make_employee()

    inactive_manager = make_employee(
        employee_id=MANAGER_ID,
        employee_code="EMP-002",
        is_active=False,
    )

    repository.get_employee_by_id.side_effect = [
        employee,
        inactive_manager,
    ]

    request = EmployeeUpdateRequest(
        manager_id=MANAGER_ID
    )

    with pytest.raises(
        ValidationError,
        match="inactive",
    ):
        await service.update_employee(
            request,
            employee_id=EMPLOYEE_ID,
        )


@pytest.mark.asyncio
async def test_manager_cycle_rejected() -> None:
    service, _, repository = make_service()

    employee = make_employee()

    proposed_manager = make_employee(
        employee_id=MANAGER_ID,
        employee_code="EMP-002",
        manager_id=EMPLOYEE_ID,
    )

    repository.get_employee_by_id.side_effect = [
        employee,
        proposed_manager,
        proposed_manager,
    ]

    request = EmployeeUpdateRequest(
        manager_id=MANAGER_ID
    )

    with pytest.raises(
        ValidationError,
        match="organizational cycle",
    ):
        await service.update_employee(
            request,
            employee_id=EMPLOYEE_ID,
        )


# =========================================================
# EMPLOYMENT LIFECYCLE
# =========================================================


@pytest.mark.asyncio
async def test_create_terminated_employee_requires_termination_date() -> None:
    with pytest.raises(
        Exception
    ):
        EmployeeCreateRequest(
            employee_code="EMP-001",
            first_name="Alice",
            last_name="Smith",
            employment_status=(
                EMPLOYMENT_STATUS_TERMINATED
            ),
        )


@pytest.mark.asyncio
async def test_termination_date_cannot_precede_hire_date() -> None:
    with pytest.raises(
        Exception
    ):
        EmployeeCreateRequest(
            employee_code="EMP-001",
            first_name="Alice",
            last_name="Smith",
            hire_date=date(2026, 5, 1),
            termination_date=date(2026, 4, 1),
        )


@pytest.mark.asyncio
async def test_terminated_employee_becomes_inactive() -> None:
    service, session, repository = make_service()

    employee = make_employee()

    updated_employee = make_employee(
        employment_status=(
            EMPLOYMENT_STATUS_TERMINATED
        ),
        termination_date=date(2026, 8, 21),
        is_active=False,
    )

    repository.get_employee_by_id.side_effect = [
        employee,
        updated_employee,
    ]

    repository.update_employee.return_value = (
        updated_employee
    )

    request = EmployeeUpdateRequest(
        employment_status=(
            EMPLOYMENT_STATUS_TERMINATED
        ),
        termination_date=date(2026, 8, 21),
    )

    response = await service.update_employee(
        request,
        employee_id=EMPLOYEE_ID,
    )

    values = (
        repository.update_employee
        .await_args.kwargs["values"]
    )

    assert (
        values["employment_status"]
        == EMPLOYMENT_STATUS_TERMINATED
    )

    assert values["is_active"] is False

    assert (
        values["termination_date"]
        == date(2026, 8, 21)
    )

    assert response.employee.is_active is False

    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_terminated_employee_cannot_be_forced_active() -> None:
    service, _, repository = make_service()

    employee = make_employee()

    repository.get_employee_by_id.return_value = (
        employee
    )

    request = EmployeeUpdateRequest(
        employment_status=(
            EMPLOYMENT_STATUS_TERMINATED
        ),
        termination_date=date(2026, 8, 21),
        is_active=True,
    )

    with pytest.raises(
        ValidationError,
        match="cannot be active",
    ):
        await service.update_employee(
            request,
            employee_id=EMPLOYEE_ID,
        )


# =========================================================
# EXPLICIT NULL PATCH SEMANTICS
# =========================================================


@pytest.mark.asyncio
async def test_update_employee_can_clear_optional_fields() -> None:
    service, session, repository = make_service()

    employee = make_employee(
        manager_id=MANAGER_ID
    )

    updated_employee = make_employee(
        work_email=None,
        department_id=None,
        team_id=None,
        manager_id=None,
    )

    repository.get_employee_by_id.side_effect = [
        employee,
        updated_employee,
    ]

    repository.update_employee.return_value = (
        updated_employee
    )

    request = EmployeeUpdateRequest(
        work_email=None,
        department_id=None,
        team_id=None,
        manager_id=None,
    )

    await service.update_employee(
        request,
        employee_id=EMPLOYEE_ID,
    )

    values = (
        repository.update_employee
        .await_args.kwargs["values"]
    )

    assert "work_email" in values
    assert values["work_email"] is None

    assert "department_id" in values
    assert values["department_id"] is None

    assert "team_id" in values
    assert values["team_id"] is None

    assert "manager_id" in values
    assert values["manager_id"] is None

    session.commit.assert_awaited_once()


# =========================================================
# NOT FOUND
# =========================================================


@pytest.mark.asyncio
async def test_get_employee_not_found() -> None:
    service, _, repository = make_service()

    repository.get_employee_by_id.return_value = None

    with pytest.raises(
        ResourceNotFound
    ):
        await service.get_employee(
            employee_id=EMPLOYEE_ID,
        )


@pytest.mark.asyncio
async def test_get_department_not_found() -> None:
    service, _, repository = make_service()

    repository.get_department_by_id.return_value = None

    with pytest.raises(
        ResourceNotFound
    ):
        await service.get_department(
            department_id=DEPARTMENT_ID,
        )


@pytest.mark.asyncio
async def test_get_team_not_found() -> None:
    service, _, repository = make_service()

    repository.get_team_by_id.return_value = None

    with pytest.raises(
        ResourceNotFound
    ):
        await service.get_team(
            team_id=TEAM_ID,
        )