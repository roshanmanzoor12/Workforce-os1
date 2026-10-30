from __future__ import annotations

import uuid

from fastapi import (
    APIRouter,
    Query,
    status,
)

from app.db.tenant_dependency import TenantScope
from app.modules.employee_records.schemas import (
    EmployeeRecordCreateRequest,
    EmployeeRecordDeleteResponse,
    EmployeeRecordListResponse,
    EmployeeRecordResponse,
    EmployeeRecordUpdateRequest,
)
from app.modules.employee_records.service import (
    EmployeeRecordService,
)
from app.modules.workspaces.models import (
    WORKSPACE_ROLE_ADMIN,
    WORKSPACE_ROLE_OWNER,
)


router = APIRouter(
    prefix="/workspaces/{workspace_id}/employee-records",
    tags=["Employee Records"],
)


def _require_manager(
    scope: TenantScope,
) -> None:
    if scope.role_key not in {
        WORKSPACE_ROLE_OWNER,
        WORKSPACE_ROLE_ADMIN,
    }:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Workspace OWNER or ADMIN role required.",
        )


def _service(
    scope: TenantScope,
) -> EmployeeRecordService:
    return EmployeeRecordService(scope.session)


@router.post(
    "/{employee_id}",
    response_model=EmployeeRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an employee record",
)
async def create_employee_record(
    employee_id: uuid.UUID,
    request: EmployeeRecordCreateRequest,
    scope: TenantScope,
) -> EmployeeRecordResponse:
    _require_manager(scope)

    return await _service(scope).create(
        employee_id=employee_id,
        request=request,
    )


@router.get(
    "/{employee_id}",
    response_model=EmployeeRecordListResponse,
    status_code=status.HTTP_200_OK,
    summary="List employee records",
)
async def list_employee_records(
    employee_id: uuid.UUID,
    scope: TenantScope,
    record_type: str | None = Query(
        default=None,
        max_length=50,
    ),
) -> EmployeeRecordListResponse:
    return await _service(scope).list(
        employee_id=employee_id,
        record_type=record_type,
    )


@router.get(
    "/record/{record_id}",
    response_model=EmployeeRecordResponse,
    status_code=status.HTTP_200_OK,
    summary="Get an employee record",
)
async def get_employee_record(
    record_id: uuid.UUID,
    scope: TenantScope,
) -> EmployeeRecordResponse:
    return await _service(scope).get(
        record_id=record_id,
    )


@router.patch(
    "/record/{record_id}",
    response_model=EmployeeRecordResponse,
    status_code=status.HTTP_200_OK,
    summary="Update an employee record",
)
async def update_employee_record(
    record_id: uuid.UUID,
    request: EmployeeRecordUpdateRequest,
    scope: TenantScope,
) -> EmployeeRecordResponse:
    _require_manager(scope)

    return await _service(scope).update(
        record_id=record_id,
        request=request,
    )


@router.delete(
    "/record/{record_id}",
    response_model=EmployeeRecordDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete an employee record",
)
async def delete_employee_record(
    record_id: uuid.UUID,
    scope: TenantScope,
) -> EmployeeRecordDeleteResponse:
    _require_manager(scope)

    return await _service(scope).delete(
        record_id=record_id,
    )


__all__ = ["router"]