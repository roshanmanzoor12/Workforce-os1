from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.modules.employees.schemas import (
    EmployeeCreateRequest,
    EmployeePublic,
    EmployeeUpdateRequest,
)
from app.modules.employees.scope_access import build_employee_access
from app.modules.employees.scoped_service import ScopedEmployeeService
from app.modules.employees.service import EmployeeService


def make_service(permissions):
    scope = SimpleNamespace(
        workspace_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        membership_id=uuid.uuid4(),
        role_key="member",
        effective_permissions=frozenset(permissions),
    )

    row = SimpleNamespace(
        id=uuid.uuid4(),
        user_id=scope.user_id,
        team_id=None,
        department_id=None,
        is_active=True,
        employment_status="active",
    )

    context = build_employee_access(scope, row)
    session = SimpleNamespace(rollback=AsyncMock())

    return ScopedEmployeeService(session, context), row


@pytest.mark.asyncio
async def test_read_permission_is_required_before_querying():
    service, own = make_service({"employees.update"})
    service.repository.get_employee_by_id = AsyncMock()

    with pytest.raises(HTTPException) as error:
        await service.get_employee(employee_id=own.id)

    assert error.value.status_code == 403
    service.repository.get_employee_by_id.assert_not_awaited()


@pytest.mark.asyncio
async def test_invisible_employee_returns_404():
    service, _ = make_service({"employees.self.read"})

    service.repository.get_employee_by_id = AsyncMock(
        return_value=None
    )

    with pytest.raises(HTTPException) as error:
        await service.get_employee(employee_id=uuid.uuid4())

    assert error.value.status_code == 404


@pytest.mark.asyncio
async def test_out_of_scope_manager_is_omitted(monkeypatch):
    service, own = make_service({"employees.self.read"})

    own.manager_id = uuid.uuid4()
    own.department = None
    own.team = None

    service.repository.get_employee_by_id = AsyncMock(
        side_effect=[own, None]
    )

    public = EmployeePublic.model_construct(id=own.id)

    monkeypatch.setattr(
        service,
        "_employee_public",
        lambda employee: public,
    )

    response = await service.get_employee(employee_id=own.id)

    assert response.employee.id == own.id
    assert response.manager is None
    assert service.repository.get_employee_by_id.await_count == 2


@pytest.mark.asyncio
async def test_limited_create_is_denied_before_business_logic(
    monkeypatch,
):
    service, _ = make_service({"employees.create"})
    create = AsyncMock()

    monkeypatch.setattr(EmployeeService, "create_employee", create)

    request = EmployeeCreateRequest(
        employee_code="E-100",
        first_name="Test",
        last_name="Employee",
    )

    with pytest.raises(HTTPException) as error:
        await service.create_employee(request)

    assert error.value.status_code == 403
    create.assert_not_awaited()


@pytest.mark.asyncio
async def test_limited_delete_is_denied_before_business_logic(
    monkeypatch,
):
    service, own = make_service({"employees.delete"})
    delete = AsyncMock()

    monkeypatch.setattr(EmployeeService, "delete_employee", delete)

    with pytest.raises(HTTPException):
        await service.delete_employee(employee_id=own.id)

    delete.assert_not_awaited()


@pytest.mark.asyncio
async def test_protected_update_is_denied_before_business_logic(
    monkeypatch,
):
    service, own = make_service({"employees.update"})
    update = AsyncMock()

    monkeypatch.setattr(EmployeeService, "update_employee", update)

    request = EmployeeUpdateRequest(user_id=uuid.uuid4())

    with pytest.raises(HTTPException):
        await service.update_employee(
            request,
            employee_id=own.id,
        )

    update.assert_not_awaited()


@pytest.mark.asyncio
async def test_invisible_update_rolls_back_and_does_not_mutate(
    monkeypatch,
):
    service, own = make_service({"employees.update"})

    service.repository.get_employee_by_id = AsyncMock(
        return_value=None
    )

    update = AsyncMock()
    monkeypatch.setattr(EmployeeService, "update_employee", update)

    with pytest.raises(HTTPException) as error:
        await service.update_employee(
            EmployeeUpdateRequest(first_name="Updated"),
            employee_id=own.id,
        )

    assert error.value.status_code == 404
    update.assert_not_awaited()
    service.session.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_linked_user_requires_membership_validation(
    monkeypatch,
):
    service, _ = make_service({
        "employees.all.read",
        "employees.create",
    })

    create = AsyncMock()
    monkeypatch.setattr(EmployeeService, "create_employee", create)

    request = EmployeeCreateRequest(
        user_id=uuid.uuid4(),
        employee_code="E-101",
        first_name="Linked",
        last_name="Employee",
    )

    with pytest.raises(HTTPException) as error:
        await service.create_employee(request)

    assert error.value.status_code == 403
    create.assert_not_awaited()


@pytest.mark.asyncio
async def test_validated_link_reaches_existing_business_service(
    monkeypatch,
):
    service, _ = make_service({
        "employees.all.read",
        "employees.create",
    })

    bridge = SimpleNamespace(
        validate_employee_user_link=AsyncMock()
    )
    service.membership_bridge = bridge

    expected = object()
    create = AsyncMock(return_value=expected)

    monkeypatch.setattr(EmployeeService, "create_employee", create)

    request = EmployeeCreateRequest(
        user_id=uuid.uuid4(),
        employee_code="E-102",
        first_name="Valid",
        last_name="Employee",
    )

    assert await service.create_employee(request) is expected

    bridge.validate_employee_user_link.assert_awaited_once_with(
        workspace_id=service.context.workspace_id,
        employee_user_id=request.user_id,
    )
    create.assert_awaited_once_with(request)


@pytest.mark.asyncio
async def test_profile_update_preserves_existing_business_service(
    monkeypatch,
):
    service, own = make_service({"employees.update"})

    service.repository.get_employee_by_id = AsyncMock(
        return_value=own
    )

    expected = object()
    update = AsyncMock(return_value=expected)

    monkeypatch.setattr(EmployeeService, "update_employee", update)

    request = EmployeeUpdateRequest(first_name="Updated")

    result = await service.update_employee(
        request,
        employee_id=own.id,
    )

    assert result is expected

    service.repository.get_employee_by_id.assert_awaited_once_with(
        own.id,
        for_update=True,
    )
    update.assert_awaited_once_with(
        request,
        employee_id=own.id,
    )