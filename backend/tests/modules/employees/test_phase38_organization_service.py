from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.modules.employees.organization_service import (
    ScopedOrganizationService,
)
from app.modules.employees.schemas import (
    DepartmentCreateRequest,
    DepartmentUpdateRequest,
    TeamCreateRequest,
    TeamUpdateRequest,
)
from app.modules.employees.service import EmployeeService
from app.modules.workspace_permissions.access_context import (
    WorkspaceAccessContext,
)
from app.modules.workspace_permissions.scopes import (
    WorkspaceResourceScope,
    WorkspaceScopeType,
)


def make_service(*, permissions=(), workspace=False):
    context = WorkspaceAccessContext(
        user_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        membership_id=uuid.uuid4(),
        employee_id=uuid.uuid4(),
        role_key="owner" if workspace else "member",
        permissions=frozenset(permissions),
        scopes=(
            (
                WorkspaceResourceScope(
                    type=WorkspaceScopeType.WORKSPACE,
                ),
            )
            if workspace
            else ()
        ),
    )

    session = SimpleNamespace(
        rollback=AsyncMock(),
    )

    return ScopedOrganizationService(session, context), session


@pytest.mark.asyncio
@pytest.mark.parametrize("resource", ["departments", "teams"])
async def test_missing_read_permission_denies_before_query(resource):
    service, _ = make_service(workspace=True)

    method = (
        "list_departments"
        if resource == "departments"
        else "list_teams"
    )

    repository_method = AsyncMock()
    setattr(service.repository, method, repository_method)

    with pytest.raises(HTTPException) as error:
        await getattr(service, method)()

    assert error.value.status_code == 403
    repository_method.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("resource", ["departments", "teams"])
async def test_out_of_scope_detail_returns_404(resource):
    service, _ = make_service(
        permissions={f"{resource}.read"},
    )

    if resource == "departments":
        service.repository.get_department_by_id = AsyncMock(
            return_value=None,
        )

        with pytest.raises(HTTPException) as error:
            await service.get_department(
                department_id=uuid.uuid4(),
            )
    else:
        service.repository.get_team_by_id = AsyncMock(
            return_value=None,
        )

        with pytest.raises(HTTPException) as error:
            await service.get_team(
                team_id=uuid.uuid4(),
            )

    assert error.value.status_code == 404


@pytest.mark.asyncio
@pytest.mark.parametrize("resource", ["departments", "teams"])
async def test_limited_management_cannot_create(resource, monkeypatch):
    service, _ = make_service(
        permissions={f"{resource}.manage"},
    )

    if resource == "departments":
        method = "create_department"
        request = DepartmentCreateRequest(name="Engineering")
    else:
        method = "create_team"
        request = TeamCreateRequest(name="Platform")

    business_method = AsyncMock()
    monkeypatch.setattr(EmployeeService, method, business_method)

    with pytest.raises(HTTPException) as error:
        await getattr(service, method)(request)

    assert error.value.status_code == 403
    business_method.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("resource", ["departments", "teams"])
async def test_workspace_management_preserves_create_business_logic(
    resource,
    monkeypatch,
):
    service, _ = make_service(
        permissions={f"{resource}.manage"},
        workspace=True,
    )

    if resource == "departments":
        method = "create_department"
        request = DepartmentCreateRequest(name="Engineering")
    else:
        method = "create_team"
        request = TeamCreateRequest(name="Platform")

    expected = object()
    business_method = AsyncMock(return_value=expected)

    monkeypatch.setattr(EmployeeService, method, business_method)

    assert await getattr(service, method)(request) is expected
    business_method.assert_awaited_once_with(request)


@pytest.mark.asyncio
@pytest.mark.parametrize("resource", ["departments", "teams"])
@pytest.mark.parametrize("action", ["update", "delete"])
async def test_missing_mutation_target_rolls_back_without_mutating(
    resource,
    action,
    monkeypatch,
):
    service, session = make_service(
        permissions={f"{resource}.manage"},
        workspace=True,
    )

    singular = "department" if resource == "departments" else "team"
    method = f"{action}_{singular}"
    lookup = f"get_{singular}_by_id"
    target_id = uuid.uuid4()

    setattr(
        service.repository,
        lookup,
        AsyncMock(return_value=None),
    )

    business_method = AsyncMock()
    monkeypatch.setattr(EmployeeService, method, business_method)

    arguments = {f"{singular}_id": target_id}

    with pytest.raises(HTTPException) as error:
        if action == "update":
            request = (
                DepartmentUpdateRequest(description="Updated")
                if singular == "department"
                else TeamUpdateRequest(description="Updated")
            )

            await getattr(service, method)(
                request,
                **arguments,
            )
        else:
            await getattr(service, method)(**arguments)

    assert error.value.status_code == 404
    business_method.assert_not_awaited()
    session.rollback.assert_awaited_once()

    getattr(service.repository, lookup).assert_awaited_once_with(
        target_id,
        for_update=True,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("resource", ["departments", "teams"])
async def test_delete_locks_target_before_business_mutation(
    resource,
    monkeypatch,
):
    service, session = make_service(
        permissions={f"{resource}.manage"},
        workspace=True,
    )

    singular = "department" if resource == "departments" else "team"
    target_id = uuid.uuid4()
    calls = []

    async def lookup(record_id, *, for_update=False):
        calls.append(("lock", record_id, for_update))
        return object()

    # This function replaces a class method, so Python passes self.
    async def delete(self, **kwargs):
        assert self is service
        calls.append(("delete", kwargs))
        return "deleted"

    setattr(
        service.repository,
        f"get_{singular}_by_id",
        lookup,
    )

    monkeypatch.setattr(
        EmployeeService,
        f"delete_{singular}",
        delete,
    )

    arguments = {f"{singular}_id": target_id}

    result = await getattr(
        service,
        f"delete_{singular}",
    )(**arguments)

    assert result == "deleted"

    assert calls == [
        ("lock", target_id, True),
        ("delete", arguments),
    ]

    session.rollback.assert_not_awaited()