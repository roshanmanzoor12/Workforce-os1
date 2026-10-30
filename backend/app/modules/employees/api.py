from __future__ import annotations

import uuid

from app.modules.employees.access_service import (
    EmployeeAccessService,
)
from app.modules.employees.schemas import (
    DepartmentCreateRequest,
    DepartmentUpdateRequest,
    EmployeeCreateRequest,
    EmployeeUpdateRequest,
    TeamCreateRequest,
    TeamUpdateRequest,
)
from app.modules.tenant_api.context import (
    AuthorizedTenantContext,
)


class EmployeeApi:
    """
    Thin application API around EmployeeAccessService.

    Keeps routers simple and makes authorization testable without
    HTTP machinery.
    """

    def __init__(
        self,
        context: AuthorizedTenantContext,
    ) -> None:
        self.context = context

        self.service = EmployeeAccessService(
            workspace_id=context.workspace_id,
            actor_user_id=context.actor_user_id,
            control_session=context.control_session,
            tenant_session=context.tenant_session,
        )

    async def create_department(
        self,
        request: DepartmentCreateRequest,
    ):
        return await self.service.create_department(
            request
        )

    async def list_departments(
        self,
        *,
        include_inactive: bool = False,
    ):
        return await self.service.list_departments(
            include_inactive=include_inactive,
        )

    async def get_department(
        self,
        department_id: uuid.UUID,
    ):
        return await self.service.get_department(
            department_id=department_id
        )

    async def update_department(
        self,
        department_id: uuid.UUID,
        request: DepartmentUpdateRequest,
    ):
        return await self.service.update_department(
            request,
            department_id=department_id,
        )

    async def delete_department(
        self,
        department_id: uuid.UUID,
    ):
        return await self.service.delete_department(
            department_id=department_id
        )

    async def create_team(
        self,
        request: TeamCreateRequest,
    ):
        return await self.service.create_team(
            request
        )

    async def list_teams(
        self,
        *,
        department_id: uuid.UUID | None = None,
        include_inactive: bool = False,
    ):
        return await self.service.list_teams(
            department_id=department_id,
            include_inactive=include_inactive,
        )

    async def get_team(
        self,
        team_id: uuid.UUID,
    ):
        return await self.service.get_team(
            team_id=team_id
        )

    async def update_team(
        self,
        team_id: uuid.UUID,
        request: TeamUpdateRequest,
    ):
        return await self.service.update_team(
            request,
            team_id=team_id,
        )

    async def delete_team(
        self,
        team_id: uuid.UUID,
    ):
        return await self.service.delete_team(
            team_id=team_id
        )

    async def create_employee(
        self,
        request: EmployeeCreateRequest,
    ):
        return await self.service.create_employee(
            request
        )

    async def list_employees(
        self,
        **filters,
    ):
        return await self.service.list_employees(
            **filters
        )

    async def get_employee(
        self,
        employee_id: uuid.UUID,
    ):
        return await self.service.get_employee(
            employee_id=employee_id
        )

    async def update_employee(
        self,
        employee_id: uuid.UUID,
        request: EmployeeUpdateRequest,
    ):
        return await self.service.update_employee(
            request,
            employee_id=employee_id,
        )

    async def delete_employee(
        self,
        employee_id: uuid.UUID,
    ):
        return await self.service.delete_employee(
            employee_id=employee_id
        )


__all__ = [
    "EmployeeApi",
]