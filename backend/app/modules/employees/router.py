from __future__ import annotations

import uuid

from fastapi import APIRouter, Query, status

from app.core.exceptions import ValidationError
from app.db.tenant_dependency import ControlDB, TenantScope
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
from app.modules.employees.scope_access import (
    resolve_employee_access,
)
from app.modules.employees.scoped_service import (
    ScopedEmployeeService,
)
from app.modules.employees.service import EmployeeService


router = APIRouter(
    prefix="/workspaces/{workspace_id}",
    tags=["Employees"],
)

EMPLOYEE_WRITE_ROLES = frozenset({"owner", "admin"})


def get_scope_role(scope: TenantScope) -> str | None:
    role_key = getattr(scope, "role_key", None)

    if isinstance(role_key, str):
        return role_key

    context = getattr(scope, "context", None)
    role_key = getattr(context, "role_key", None)

    return role_key if isinstance(role_key, str) else None


def require_employee_write_access(scope: TenantScope) -> None:
    # Retained for compatibility with existing callers.
    # Organization routes below use effective permissions and scopes.
    if get_scope_role(scope) not in EMPLOYEE_WRITE_ROLES:
        raise ValidationError(
            "Owner or admin workspace role is required "
            "to manage organization data."
        )


def get_employee_service(scope: TenantScope) -> EmployeeService:
    # Retained for compatibility. Routes use scoped factories.
    return EmployeeService(scope.session)


async def get_scoped_employee_service(
    scope: TenantScope,
    control_session=None,
) -> ScopedEmployeeService:
    context = await resolve_employee_access(scope)

    bridge = (
        EmployeeMembershipBridge(control_session)
        if control_session is not None
        else None
    )

    return ScopedEmployeeService(
        scope.session,
        context,
        membership_bridge=bridge,
    )


async def get_scoped_organization_service(
    scope: TenantScope,
) -> ScopedOrganizationService:
    context = await resolve_employee_access(scope)

    return ScopedOrganizationService(
        scope.session,
        context,
    )


@router.post(
    "/departments",
    response_model=DepartmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create department",
)
async def create_department(
    payload: DepartmentCreateRequest,
    scope: TenantScope,
) -> DepartmentResponse:
    service = await get_scoped_organization_service(scope)
    return await service.create_department(payload)


@router.get(
    "/departments",
    response_model=DepartmentListResponse,
    summary="List departments",
)
async def list_departments(
    scope: TenantScope,
    include_inactive: bool = Query(default=False),
) -> DepartmentListResponse:
    service = await get_scoped_organization_service(scope)

    return await service.list_departments(
        include_inactive=include_inactive,
    )


@router.get(
    "/departments/{department_id}",
    response_model=DepartmentResponse,
    summary="Get department",
)
async def get_department(
    department_id: uuid.UUID,
    scope: TenantScope,
) -> DepartmentResponse:
    service = await get_scoped_organization_service(scope)

    return await service.get_department(
        department_id=department_id,
    )


@router.patch(
    "/departments/{department_id}",
    response_model=DepartmentResponse,
    summary="Update department",
)
async def update_department(
    department_id: uuid.UUID,
    payload: DepartmentUpdateRequest,
    scope: TenantScope,
) -> DepartmentResponse:
    service = await get_scoped_organization_service(scope)

    return await service.update_department(
        payload,
        department_id=department_id,
    )


@router.delete(
    "/departments/{department_id}",
    response_model=DepartmentDeleteResponse,
    summary="Deactivate department",
)
async def delete_department(
    department_id: uuid.UUID,
    scope: TenantScope,
) -> DepartmentDeleteResponse:
    service = await get_scoped_organization_service(scope)

    return await service.delete_department(
        department_id=department_id,
    )


@router.post(
    "/teams",
    response_model=TeamResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create team",
)
async def create_team(
    payload: TeamCreateRequest,
    scope: TenantScope,
) -> TeamResponse:
    service = await get_scoped_organization_service(scope)
    return await service.create_team(payload)


@router.get(
    "/teams",
    response_model=TeamListResponse,
    summary="List teams",
)
async def list_teams(
    scope: TenantScope,
    department_id: uuid.UUID | None = Query(default=None),
    include_inactive: bool = Query(default=False),
) -> TeamListResponse:
    service = await get_scoped_organization_service(scope)

    return await service.list_teams(
        department_id=department_id,
        include_inactive=include_inactive,
    )


@router.get(
    "/teams/{team_id}",
    response_model=TeamResponse,
    summary="Get team",
)
async def get_team(
    team_id: uuid.UUID,
    scope: TenantScope,
) -> TeamResponse:
    service = await get_scoped_organization_service(scope)

    return await service.get_team(team_id=team_id)


@router.patch(
    "/teams/{team_id}",
    response_model=TeamResponse,
    summary="Update team",
)
async def update_team(
    team_id: uuid.UUID,
    payload: TeamUpdateRequest,
    scope: TenantScope,
) -> TeamResponse:
    service = await get_scoped_organization_service(scope)

    return await service.update_team(
        payload,
        team_id=team_id,
    )


@router.delete(
    "/teams/{team_id}",
    response_model=TeamDeleteResponse,
    summary="Deactivate team",
)
async def delete_team(
    team_id: uuid.UUID,
    scope: TenantScope,
) -> TeamDeleteResponse:
    service = await get_scoped_organization_service(scope)

    return await service.delete_team(team_id=team_id)


@router.post(
    "/employees",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create employee",
)
async def create_employee(
    payload: EmployeeCreateRequest,
    scope: TenantScope,
    control_session: ControlDB,
) -> EmployeeResponse:
    service = await get_scoped_employee_service(
        scope,
        control_session,
    )

    return await service.create_employee(payload)


@router.get(
    "/employees",
    response_model=EmployeeListResponse,
    summary="List employees",
)
async def list_employees(
    scope: TenantScope,
    department_id: uuid.UUID | None = Query(default=None),
    team_id: uuid.UUID | None = Query(default=None),
    manager_id: uuid.UUID | None = Query(default=None),
    employment_status: str | None = Query(default=None),
    include_inactive: bool = Query(default=False),
    search: str | None = Query(default=None, max_length=200),
) -> EmployeeListResponse:
    service = await get_scoped_employee_service(scope)

    return await service.list_employees(
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
    summary="Get employee",
)
async def get_employee(
    employee_id: uuid.UUID,
    scope: TenantScope,
) -> EmployeeDetailResponse:
    service = await get_scoped_employee_service(scope)

    return await service.get_employee(employee_id=employee_id)


@router.patch(
    "/employees/{employee_id}",
    response_model=EmployeeResponse,
    summary="Update employee",
)
async def update_employee(
    employee_id: uuid.UUID,
    payload: EmployeeUpdateRequest,
    scope: TenantScope,
    control_session: ControlDB,
) -> EmployeeResponse:
    service = await get_scoped_employee_service(
        scope,
        control_session,
    )

    return await service.update_employee(
        payload,
        employee_id=employee_id,
    )


@router.delete(
    "/employees/{employee_id}",
    response_model=EmployeeDeleteResponse,
    summary="Deactivate employee",
)
async def delete_employee(
    employee_id: uuid.UUID,
    scope: TenantScope,
) -> EmployeeDeleteResponse:
    service = await get_scoped_employee_service(scope)

    return await service.delete_employee(employee_id=employee_id)


__all__ = [
    "EMPLOYEE_WRITE_ROLES",
    "get_scope_role",
    "require_employee_write_access",
    "get_employee_service",
    "get_scoped_employee_service",
    "get_scoped_organization_service",
    "router",
]