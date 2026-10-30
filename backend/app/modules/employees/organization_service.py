from __future__ import annotations

import uuid

from fastapi import HTTPException, status

from app.modules.employees.organization_policy import (
    require_organization_permission,
)
from app.modules.employees.organization_repository import (
    ScopedOrganizationRepository,
)
from app.modules.employees.schemas import (
    DepartmentCreateRequest,
    DepartmentDeleteResponse,
    DepartmentListResponse,
    DepartmentResponse,
    DepartmentUpdateRequest,
    TeamCreateRequest,
    TeamDeleteResponse,
    TeamListResponse,
    TeamResponse,
    TeamUpdateRequest,
)
from app.modules.employees.service import EmployeeService
from app.modules.workspace_permissions.access_context import (
    WorkspaceAccessContext,
)


class ScopedOrganizationService(EmployeeService):
    def __init__(
        self,
        session,
        context: WorkspaceAccessContext,
    ) -> None:
        super().__init__(session)

        self.context = context
        self.repository = ScopedOrganizationRepository(
            session,
            context,
        )

    def _require_permission(
        self,
        resource: str,
        *,
        manage: bool = False,
    ) -> None:
        require_organization_permission(
            self.context,
            resource=resource,
            manage=manage,
        )

    async def _require_department(
        self,
        department_id: uuid.UUID,
    ):
        department = await self.repository.get_department_by_id(
            department_id,
        )

        if department is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Department was not found.",
            )

        return department

    async def _require_team(
        self,
        team_id: uuid.UUID,
    ):
        team = await self.repository.get_team_by_id(team_id)

        if team is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team was not found.",
            )

        return team

    async def _lock_department(
        self,
        department_id: uuid.UUID,
    ) -> None:
        department = await self.repository.get_department_by_id(
            department_id,
            for_update=True,
        )

        if department is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Department was not found.",
            )

    async def _lock_team(
        self,
        team_id: uuid.UUID,
    ) -> None:
        team = await self.repository.get_team_by_id(
            team_id,
            for_update=True,
        )

        if team is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team was not found.",
            )

    async def create_department(
        self,
        request: DepartmentCreateRequest,
    ) -> DepartmentResponse:
        self._require_permission("departments", manage=True)
        return await super().create_department(request)

    async def list_departments(
        self,
        *,
        include_inactive: bool = False,
    ) -> DepartmentListResponse:
        self._require_permission("departments")

        return await super().list_departments(
            include_inactive=include_inactive,
        )

    async def get_department(
        self,
        *,
        department_id: uuid.UUID,
    ) -> DepartmentResponse:
        self._require_permission("departments")

        return await super().get_department(
            department_id=department_id,
        )

    async def update_department(
        self,
        request: DepartmentUpdateRequest,
        *,
        department_id: uuid.UUID,
    ) -> DepartmentResponse:
        self._require_permission("departments", manage=True)

        try:
            await self._lock_department(department_id)

            return await super().update_department(
                request,
                department_id=department_id,
            )
        except Exception:
            await self.session.rollback()
            raise

    async def delete_department(
        self,
        *,
        department_id: uuid.UUID,
    ) -> DepartmentDeleteResponse:
        self._require_permission("departments", manage=True)

        try:
            await self._lock_department(department_id)

            return await super().delete_department(
                department_id=department_id,
            )
        except Exception:
            await self.session.rollback()
            raise

    async def create_team(
        self,
        request: TeamCreateRequest,
    ) -> TeamResponse:
        self._require_permission("teams", manage=True)
        return await super().create_team(request)

    async def list_teams(
        self,
        *,
        department_id: uuid.UUID | None = None,
        include_inactive: bool = False,
    ) -> TeamListResponse:
        self._require_permission("teams")

        return await super().list_teams(
            department_id=department_id,
            include_inactive=include_inactive,
        )

    async def get_team(
        self,
        *,
        team_id: uuid.UUID,
    ) -> TeamResponse:
        self._require_permission("teams")

        return await super().get_team(team_id=team_id)

    async def update_team(
        self,
        request: TeamUpdateRequest,
        *,
        team_id: uuid.UUID,
    ) -> TeamResponse:
        self._require_permission("teams", manage=True)

        try:
            await self._lock_team(team_id)

            return await super().update_team(
                request,
                team_id=team_id,
            )
        except Exception:
            await self.session.rollback()
            raise

    async def delete_team(
        self,
        *,
        team_id: uuid.UUID,
    ) -> TeamDeleteResponse:
        self._require_permission("teams", manage=True)

        try:
            await self._lock_team(team_id)

            return await super().delete_team(team_id=team_id)
        except Exception:
            await self.session.rollback()
            raise


__all__ = ["ScopedOrganizationService"]