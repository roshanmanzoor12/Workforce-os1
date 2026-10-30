from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

import app.modules.leave.integration_router as module


class FakePermissionService:
    permissions: set[str] = set()

    def __init__(
        self,
        scope,
    ) -> None:
        self.scope = scope

    def has(
        self,
        permission: str,
    ) -> bool:
        return (
            permission
            in self.permissions
        )


class FakeEmployeeRepository:
    actor = None
    target = None

    def __init__(
        self,
        session,
    ) -> None:
        self.session = session

    async def get_employee_by_id(
        self,
        employee_id,
    ):
        if (
            self.target is not None
            and self.target.id
            == employee_id
        ):
            return self.target

        return None

    async def get_employee_by_user_id(
        self,
        user_id,
    ):
        if (
            self.actor is not None
            and self.actor.user_id
            == user_id
        ):
            return self.actor

        return None


@pytest.fixture
def ids():
    return SimpleNamespace(
        actor_employee=uuid.uuid4(),
        actor_user=uuid.uuid4(),
        target_employee=uuid.uuid4(),
        team=uuid.uuid4(),
    )


@pytest.fixture
def scope(ids):
    return SimpleNamespace(
        session=object(),
        user_id=ids.actor_user,
        role_key="member",
    )


@pytest.fixture(autouse=True)
def patch_services(
    monkeypatch,
):
    FakePermissionService.permissions = (
        set()
    )

    FakeEmployeeRepository.actor = None
    FakeEmployeeRepository.target = None

    monkeypatch.setattr(
        module,
        "WorkspacePermissionService",
        FakePermissionService,
    )

    monkeypatch.setattr(
        module,
        "EmployeeRepository",
        FakeEmployeeRepository,
    )


@pytest.mark.asyncio
async def test_self_scope_allowed(
    ids,
    scope,
):
    employee = SimpleNamespace(
        id=ids.actor_employee,
        user_id=ids.actor_user,
        manager_id=None,
        team_id=ids.team,
    )

    FakeEmployeeRepository.actor = (
        employee
    )

    FakeEmployeeRepository.target = (
        employee
    )

    FakePermissionService.permissions = {
        "leave.self.read",
    }

    result = await (
        module
        ._require_employee_leave_read(
            scope,
            ids.actor_employee,
        )
    )

    assert result.id == (
        ids.actor_employee
    )


@pytest.mark.asyncio
async def test_direct_report_team_scope_allowed(
    ids,
    scope,
):
    actor = SimpleNamespace(
        id=ids.actor_employee,
        user_id=ids.actor_user,
        manager_id=None,
        team_id=ids.team,
    )

    target = SimpleNamespace(
        id=ids.target_employee,
        user_id=uuid.uuid4(),
        manager_id=(
            ids.actor_employee
        ),
        team_id=uuid.uuid4(),
    )

    FakeEmployeeRepository.actor = (
        actor
    )

    FakeEmployeeRepository.target = (
        target
    )

    FakePermissionService.permissions = {
        "leave.team.read",
    }

    result = await (
        module
        ._require_employee_leave_read(
            scope,
            ids.target_employee,
        )
    )

    assert result.id == (
        ids.target_employee
    )


@pytest.mark.asyncio
async def test_same_team_scope_allowed(
    ids,
    scope,
):
    actor = SimpleNamespace(
        id=ids.actor_employee,
        user_id=ids.actor_user,
        manager_id=None,
        team_id=ids.team,
    )

    target = SimpleNamespace(
        id=ids.target_employee,
        user_id=uuid.uuid4(),
        manager_id=None,
        team_id=ids.team,
    )

    FakeEmployeeRepository.actor = (
        actor
    )

    FakeEmployeeRepository.target = (
        target
    )

    FakePermissionService.permissions = {
        "leave.team.read",
    }

    result = await (
        module
        ._require_employee_leave_read(
            scope,
            ids.target_employee,
        )
    )

    assert result.id == (
        ids.target_employee
    )


@pytest.mark.asyncio
async def test_all_scope_allowed(
    ids,
    scope,
):
    target = SimpleNamespace(
        id=ids.target_employee,
        user_id=uuid.uuid4(),
        manager_id=None,
        team_id=None,
    )

    FakeEmployeeRepository.target = (
        target
    )

    FakePermissionService.permissions = {
        "leave.all.read",
    }

    result = await (
        module
        ._require_employee_leave_read(
            scope,
            ids.target_employee,
        )
    )

    assert result.id == (
        ids.target_employee
    )


@pytest.mark.asyncio
async def test_out_of_scope_denied(
    ids,
    scope,
):
    actor = SimpleNamespace(
        id=ids.actor_employee,
        user_id=ids.actor_user,
        manager_id=None,
        team_id=uuid.uuid4(),
    )

    target = SimpleNamespace(
        id=ids.target_employee,
        user_id=uuid.uuid4(),
        manager_id=None,
        team_id=uuid.uuid4(),
    )

    FakeEmployeeRepository.actor = (
        actor
    )

    FakeEmployeeRepository.target = (
        target
    )

    FakePermissionService.permissions = {
        "leave.team.read",
    }

    with pytest.raises(
        HTTPException
    ) as exc:
        await (
            module
            ._require_employee_leave_read(
                scope,
                ids.target_employee,
            )
        )

    assert (
        exc.value.status_code
        == 403
    )


@pytest.mark.asyncio
async def test_missing_target_is_404(
    ids,
    scope,
):
    FakePermissionService.permissions = {
        "leave.all.read",
    }

    with pytest.raises(
        HTTPException
    ) as exc:
        await (
            module
            ._require_employee_leave_read(
                scope,
                ids.target_employee,
            )
        )

    assert (
        exc.value.status_code
        == 404
    )