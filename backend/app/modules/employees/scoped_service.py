from __future__ import annotations

import uuid

from fastapi import HTTPException

from app.modules.employees.schemas import (
    EmployeeCreateRequest,
    EmployeeDetailResponse,
    EmployeeUpdateRequest,
)
from app.modules.employees.scope_access import (
    require_employee_action,
    require_employee_read,
    require_employee_update_fields,
    require_employee_workspace_scope,
)
from app.modules.employees.scoped_repository import (
    ScopedEmployeeRepository,
)
from app.modules.employees.service import EmployeeService
from app.modules.workspace_permissions.access_context import (
    WorkspaceAccessContext,
)


class ScopedEmployeeService(EmployeeService):
    def __init__(
        self,
        session,
        context: WorkspaceAccessContext,
        *,
        membership_bridge=None,
    ) -> None:
        super().__init__(session)
        self.context = context
        self.membership_bridge = membership_bridge
        self.repository = ScopedEmployeeRepository(session, context)

    async def _require_employee(self, employee_id: uuid.UUID):
        employee = await self.repository.get_employee_by_id(employee_id)

        if employee is None:
            raise HTTPException(
                status_code=404,
                detail="Employee was not found.",
            )

        return employee

    async def _lock_employee(self, employee_id: uuid.UUID):
        employee = await self.repository.get_employee_by_id(
            employee_id,
            for_update=True,
        )

        if employee is None:
            raise HTTPException(
                status_code=404,
                detail="Employee was not found.",
            )

        return employee

    async def _validate_user_link(
        self,
        user_id: uuid.UUID | None,
    ) -> None:
        if user_id is None:
            return

        if self.membership_bridge is None:
            raise HTTPException(
                status_code=403,
                detail="Employee membership validation is unavailable.",
            )

        await self.membership_bridge.validate_employee_user_link(
            workspace_id=self.context.workspace_id,
            employee_user_id=user_id,
        )

    async def list_employees(
        self,
        *,
        department_id: uuid.UUID | None = None,
        team_id: uuid.UUID | None = None,
        manager_id: uuid.UUID | None = None,
        employment_status: str | None = None,
        include_inactive: bool = False,
        search: str | None = None,
    ):
        require_employee_read(self.context)

        return await super().list_employees(
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
        require_employee_read(self.context)
        employee = await self._require_employee(employee_id)

        manager = None

        if employee.manager_id is not None:
            manager = await self.repository.get_employee_by_id(
                employee.manager_id
            )

        return EmployeeDetailResponse(
            employee=self._employee_public(employee),
            department=(
                self._department_public(employee.department)
                if employee.department is not None
                else None
            ),
            team=(
                self._team_public(employee.team)
                if employee.team is not None
                else None
            ),
            manager=(
                self._employee_public(manager)
                if manager is not None
                else None
            ),
        )

    async def create_employee(
        self,
        request: EmployeeCreateRequest,
    ):
        require_employee_action(self.context, "create")
        require_employee_workspace_scope(self.context)
        await self._validate_user_link(request.user_id)

        return await super().create_employee(request)

    async def update_employee(
        self,
        request: EmployeeUpdateRequest,
        *,
        employee_id: uuid.UUID,
    ):
        require_employee_action(self.context, "update")
        require_employee_update_fields(
            self.context,
            set(request.model_fields_set),
        )

        try:
            await self._lock_employee(employee_id)

            if "user_id" in request.model_fields_set:
                await self._validate_user_link(request.user_id)

            return await super().update_employee(
                request,
                employee_id=employee_id,
            )
        except Exception:
            await self.session.rollback()
            raise

    async def delete_employee(
        self,
        *,
        employee_id: uuid.UUID,
    ):
        require_employee_action(self.context, "delete")
        require_employee_workspace_scope(self.context)

        try:
            await self._lock_employee(employee_id)

            return await super().delete_employee(
                employee_id=employee_id
            )
        except Exception:
            await self.session.rollback()
            raise


__all__ = ["ScopedEmployeeService"]