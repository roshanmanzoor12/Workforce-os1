from __future__ import annotations

import uuid
from types import SimpleNamespace

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.employees.membership_bridge import (
    EmployeeMembershipBridge,
)
from app.modules.employees.organization_service import (
    ScopedOrganizationService,
)
from app.modules.employees.schemas import (
    DepartmentCreateRequest,
    DepartmentDeleteResponse,
    DepartmentListResponse,
    DepartmentResponse,
    DepartmentUpdateRequest,
    EmployeeCreateRequest,
    EmployeeDeleteResponse,
    EmployeeDetailResponse,
    EmployeeListResponse,
    EmployeeResponse,
    EmployeeUpdateRequest,
    TeamCreateRequest,
    TeamDeleteResponse,
    TeamListResponse,
    TeamResponse,
    TeamUpdateRequest,
)
from app.modules.employees.scope_access import resolve_employee_access
from app.modules.employees.scoped_service import ScopedEmployeeService
from app.modules.employees.service import EmployeeService
from app.modules.workspace_permissions.effective import (
    resolve_membership_permissions,
)


class EmployeeAccessService:
    """
    Resolve membership and effective permissions before tenant access.

    The server-owned control session also enables saved-scope loading
    inside resolve_employee_access.
    """

    def __init__(
        self,
        *,
        workspace_id: uuid.UUID,
        actor_user_id: uuid.UUID,
        control_session: AsyncSession,
        tenant_session: AsyncSession,
    ) -> None:
        self.workspace_id = workspace_id
        self.actor_user_id = actor_user_id
        self.control_session = control_session
        self.tenant_session = tenant_session
        self.access = EmployeeMembershipBridge(control_session)

        # Retained for compatibility. Public methods use scoped services.
        self.employees = EmployeeService(tenant_session)

    async def _resolve_access_context(self):
        membership = await self.access.require_active_member(
            workspace_id=self.workspace_id,
            user_id=self.actor_user_id,
        )

        effective_permissions = await resolve_membership_permissions(
            self.control_session,
            workspace_id=self.workspace_id,
            membership=membership,
        )

        scope = SimpleNamespace(
            workspace_id=self.workspace_id,
            user_id=self.actor_user_id,
            membership_id=membership.id,
            role_key=membership.role_key,
            effective_permissions=effective_permissions,
            session=self.tenant_session,
            control_session=self.control_session,
        )

        return await resolve_employee_access(scope)

    async def _scoped_employee_service(self) -> ScopedEmployeeService:
        context = await self._resolve_access_context()

        return ScopedEmployeeService(
            self.tenant_session,
            context,
            membership_bridge=self.access,
        )

    async def _scoped_organization_service(
        self,
    ) -> ScopedOrganizationService:
        context = await self._resolve_access_context()

        return ScopedOrganizationService(
            self.tenant_session,
            context,
        )

    async def create_department(
        self,
        request: DepartmentCreateRequest,
    ) -> DepartmentResponse:
        service = await self._scoped_organization_service()
        return await service.create_department(request)

    async def list_departments(
        self,
        *,
        include_inactive: bool = False,
    ) -> DepartmentListResponse:
        service = await self._scoped_organization_service()
        return await service.list_departments(
            include_inactive=include_inactive,
        )

    async def get_department(
        self,
        *,
        department_id: uuid.UUID,
    ) -> DepartmentResponse:
        service = await self._scoped_organization_service()
        return await service.get_department(
            department_id=department_id,
        )

    async def update_department(
        self,
        request: DepartmentUpdateRequest,
        *,
        department_id: uuid.UUID,
    ) -> DepartmentResponse:
        service = await self._scoped_organization_service()
        return await service.update_department(
            request,
            department_id=department_id,
        )

    async def delete_department(
        self,
        *,
        department_id: uuid.UUID,
    ) -> DepartmentDeleteResponse:
        service = await self._scoped_organization_service()
        return await service.delete_department(
            department_id=department_id,
        )

    async def create_team(
        self,
        request: TeamCreateRequest,
    ) -> TeamResponse:
        service = await self._scoped_organization_service()
        return await service.create_team(request)

    async def list_teams(
        self,
        *,
        department_id: uuid.UUID | None = None,
        include_inactive: bool = False,
    ) -> TeamListResponse:
        service = await self._scoped_organization_service()
        return await service.list_teams(
            department_id=department_id,
            include_inactive=include_inactive,
        )

    async def get_team(
        self,
        *,
        team_id: uuid.UUID,
    ) -> TeamResponse:
        service = await self._scoped_organization_service()
        return await service.get_team(team_id=team_id)

    async def update_team(
        self,
        request: TeamUpdateRequest,
        *,
        team_id: uuid.UUID,
    ) -> TeamResponse:
        service = await self._scoped_organization_service()
        return await service.update_team(
            request,
            team_id=team_id,
        )

    async def delete_team(
        self,
        *,
        team_id: uuid.UUID,
    ) -> TeamDeleteResponse:
        service = await self._scoped_organization_service()
        return await service.delete_team(team_id=team_id)

    async def create_employee(
        self,
        request: EmployeeCreateRequest,
    ) -> EmployeeResponse:
        service = await self._scoped_employee_service()
        return await service.create_employee(request)

    async def list_employees(
        self,
        *,
        department_id: uuid.UUID | None = None,
        team_id: uuid.UUID | None = None,
        manager_id: uuid.UUID | None = None,
        employment_status: str | None = None,
        include_inactive: bool = False,
        search: str | None = None,
    ) -> EmployeeListResponse:
        service = await self._scoped_employee_service()
        return await service.list_employees(
            department_id=department_id,
            team_id=team_id,
            manager_id=manager_id,
            employment_status=employment_status,
            include_inactive=include_inactive,
            search=search,
        )

    async def get_employee(
        self,
        *,
        employee_id: uuid.UUID,
    ) -> EmployeeDetailResponse:
        service = await self._scoped_employee_service()
        return await service.get_employee(employee_id=employee_id)

    async def update_employee(
        self,
        request: EmployeeUpdateRequest,
        *,
        employee_id: uuid.UUID,
    ) -> EmployeeResponse:
        service = await self._scoped_employee_service()
        return await service.update_employee(
            request,
            employee_id=employee_id,
        )

    async def delete_employee(
        self,
        *,
        employee_id: uuid.UUID,
    ) -> EmployeeDeleteResponse:
        service = await self._scoped_employee_service()
        return await service.delete_employee(employee_id=employee_id)


__all__ = ["EmployeeAccessService"]