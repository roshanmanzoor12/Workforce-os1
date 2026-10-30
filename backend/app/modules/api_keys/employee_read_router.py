from __future__ import annotations

from typing import Annotated, AsyncIterator
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_control_db
from app.core.exceptions import ResourceNotFound
from app.db.tenant_context import authorized_tenant_session
from app.db.tenant_dependency import TenantRequestScope
from app.modules.api_keys.authentication import (
    APIKeyPrincipal,
    authentication_error,
)
from app.modules.api_keys.authentication_dependency import (
    require_api_key,
)
from app.modules.employees.schemas import (
    EmployeeDetailResponse,
    EmployeeListResponse,
)
from app.modules.employees.service import EmployeeService
from app.modules.workspace_permissions.service import (
    WorkspacePermissionService,
)


employee_key_authentication = require_api_key("employees.read")


async def get_employee_key_scope(
    workspace_id: UUID,
    principal: Annotated[
        APIKeyPrincipal,
        Depends(employee_key_authentication),
    ],
    control_session: Annotated[
        AsyncSession,
        Depends(get_control_db),
    ],
) -> AsyncIterator[TenantRequestScope]:
    if principal.workspace_id != workspace_id:
        raise authentication_error()

    principal.require("employees.read")

    try:
        async with authorized_tenant_session(
            control_session,
            workspace_id=workspace_id,
            user_id=principal.user_id,
        ) as (context, session):
            if context.membership_id != principal.membership_id:
                raise authentication_error()

            # Recheck current membership permissions before business access.
            WorkspacePermissionService(context).require(
                "employees.read"
            )

            yield TenantRequestScope(
                context=context,
                session=session,
            )

    except ResourceNotFound:
        raise HTTPException(
            status_code=404,
            detail="Requested resource was not found.",
        ) from None


EmployeeKeyScope = Annotated[
    TenantRequestScope,
    Depends(get_employee_key_scope),
]


router = APIRouter(
    prefix="/workspaces/{workspace_id}/integrations",
    tags=["API key employee reads"],
)


@router.get(
    "/employees",
    response_model=EmployeeListResponse,
)
async def list_integration_employees(
    scope: EmployeeKeyScope,
    response: Response,
    department_id: UUID | None = Query(default=None),
    team_id: UUID | None = Query(default=None),
    manager_id: UUID | None = Query(default=None),
    employment_status: str | None = Query(default=None),
    include_inactive: bool = Query(default=False),
    search: str | None = Query(default=None, max_length=200),
) -> EmployeeListResponse:
    response.headers["Cache-Control"] = "no-store"

    return await EmployeeService(scope.session).list_employees(
        department_id=department_id,
        team_id=team_id,
        manager_id=manager_id,
        employment_status=employment_status,
        include_inactive=include_inactive,
        search=search,
    )


@router.get(
    "/employees/{employee_id}",
    response_model=EmployeeDetailResponse,
)
async def get_integration_employee(
    employee_id: UUID,
    scope: EmployeeKeyScope,
    response: Response,
) -> EmployeeDetailResponse:
    response.headers["Cache-Control"] = "no-store"

    return await EmployeeService(scope.session).get_employee(
        employee_id=employee_id,
    )