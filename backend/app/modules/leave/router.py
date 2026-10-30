from __future__ import annotations

import uuid
from datetime import date

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    status,
)

from app.db.tenant_dependency import (
    ControlDB,
    TenantScope,
)
from app.modules.leave.access_service import (
    LeaveAccessService,
)
from app.modules.leave.audit import (
    audit_leave_balance_adjusted,
    audit_leave_policy_updated,
    audit_leave_request_cancelled,
    audit_leave_request_created,
    audit_leave_request_decision,
)
from app.modules.leave.models import (
    LeaveRequestStatus,
)
from app.modules.leave.permissions import (
    LEAVE_ALL_READ,
    LEAVE_MANAGE,
    LEAVE_POLICY_MANAGE,
    LEAVE_SELF_READ,
    LEAVE_TEAM_READ,
    LEAVE_VIEW,
)
from app.modules.leave.schemas import (
    LeaveBalanceAdjustmentRequest,
    LeaveBalanceResponse,
    LeaveDecisionRequest,
    LeavePolicyResponse,
    LeavePolicyUpsertRequest,
    LeaveRequestCreateRequest,
    LeaveRequestResponse,
    LeaveTypeCreateRequest,
    LeaveTypeResponse,
    LeaveTypeUpdateRequest,
)
from app.modules.leave.service import (
    LeaveService,
)
from app.modules.workspace_permissions.service import (
    WorkspacePermissionService,
)


router = APIRouter(
    prefix=(
        "/workspaces/{workspace_id}/leave"
    ),
    tags=["Leave"],
)


# =========================================================
# HELPERS
# =========================================================


def permission_service(
    scope: TenantScope,
) -> WorkspacePermissionService:
    return WorkspacePermissionService(
        scope
    )


def access_service(
    scope: TenantScope,
) -> LeaveAccessService:
    permissions = (
        permission_service(
            scope
        )
    )

    return LeaveAccessService(
        tenant_session=scope.session,
        actor_user_id=scope.user_id,
        permission_service=permissions,
    )


# =========================================================
# TYPES
# =========================================================


@router.get(
    "/types",
    response_model=list[
        LeaveTypeResponse
    ],
)
async def list_leave_types(
    scope: TenantScope,
    active_only: bool = Query(
        default=True
    ),
):
    permission_service(
        scope
    ).require_any(
        {
            LEAVE_VIEW,
            LEAVE_SELF_READ,
            LEAVE_TEAM_READ,
            LEAVE_ALL_READ,
        }
    )

    return await (
        LeaveService(
            scope.session
        )
        .repository
        .list_types(
            active_only=active_only
        )
    )


@router.post(
    "/types",
    response_model=(
        LeaveTypeResponse
    ),
    status_code=(
        status.HTTP_201_CREATED
    ),
)
async def create_leave_type(
    request: LeaveTypeCreateRequest,
    scope: TenantScope,
):
    permission_service(
        scope
    ).require(
        LEAVE_MANAGE
    )

    return await LeaveService(
        scope.session
    ).create_leave_type(
        request
    )


@router.patch(
    "/types/{leave_type_id}",
    response_model=(
        LeaveTypeResponse
    ),
)
async def update_leave_type(
    leave_type_id: uuid.UUID,
    request: LeaveTypeUpdateRequest,
    scope: TenantScope,
):
    permission_service(
        scope
    ).require(
        LEAVE_MANAGE
    )

    return await LeaveService(
        scope.session
    ).update_leave_type(
        leave_type_id=(
            leave_type_id
        ),
        request=request,
    )


# =========================================================
# POLICIES
# =========================================================


@router.get(
    "/policies",
    response_model=list[
        LeavePolicyResponse
    ],
)
async def list_leave_policies(
    scope: TenantScope,
):
    permission_service(
        scope
    ).require_any(
        {
            LEAVE_VIEW,
            LEAVE_ALL_READ,
            LEAVE_POLICY_MANAGE,
        }
    )

    return await (
        LeaveService(
            scope.session
        )
        .repository
        .list_policies()
    )


@router.put(
    "/policies/{leave_type_id}",
    response_model=(
        LeavePolicyResponse
    ),
)
async def upsert_leave_policy(
    leave_type_id: uuid.UUID,
    request: LeavePolicyUpsertRequest,
    scope: TenantScope,
    control_session: ControlDB,
):
    access_service(
        scope
    ).require_policy_manage()

    policy = await LeaveService(
        scope.session
    ).upsert_policy(
        leave_type_id=leave_type_id,
        request=request,
    )

    await audit_leave_policy_updated(
        control_session=(
            control_session
        ),
        workspace_id=(
            scope.workspace_id
        ),
        actor_user_id=(
            scope.user_id
        ),
        leave_type_id=(
            leave_type_id
        ),
    )

    return policy


# =========================================================
# MY REQUESTS
# =========================================================


@router.get(
    "/me/requests",
    response_model=list[
        LeaveRequestResponse
    ],
)
async def list_my_leave_requests(
    scope: TenantScope,
    request_status: (
        LeaveRequestStatus | None
    ) = Query(
        default=None,
        alias="status",
    ),
    start_date: (
        date | None
    ) = Query(
        default=None
    ),
    end_date: (
        date | None
    ) = Query(
        default=None
    ),
):
    employee = await (
        access_service(
            scope
        )
        .require_self_employee()
    )

    return await (
        LeaveService(
            scope.session
        )
        .repository
        .list_requests(
            employee_id=employee.id,
            status=request_status,
            start_date=start_date,
            end_date=end_date,
        )
    )


@router.post(
    "/me/requests",
    response_model=(
        LeaveRequestResponse
    ),
    status_code=(
        status.HTTP_201_CREATED
    ),
)
async def create_my_leave_request(
    request: LeaveRequestCreateRequest,
    scope: TenantScope,
    control_session: ControlDB,
):
    employee = await (
        access_service(
            scope
        )
        .require_self_employee()
    )

    leave_request = await (
        LeaveService(
            scope.session
        )
        .create_request(
            employee_id=employee.id,
            actor_user_id=(
                scope.user_id
            ),
            request=request,
        )
    )

    await audit_leave_request_created(
        control_session=(
            control_session
        ),
        workspace_id=(
            scope.workspace_id
        ),
        actor_user_id=(
            scope.user_id
        ),
        leave_request=(
            leave_request
        ),
    )

    return leave_request


@router.post(
    "/me/requests/{request_id}/cancel",
    response_model=(
        LeaveRequestResponse
    ),
)
async def cancel_my_leave_request(
    request_id: uuid.UUID,
    scope: TenantScope,
    control_session: ControlDB,
):
    employee = await (
        access_service(
            scope
        )
        .require_self_employee()
    )

    service = LeaveService(
        scope.session
    )

    existing = await (
        service.repository
        .get_request(
            request_id
        )
    )

    if existing is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Leave request not found."
            ),
        )

    if (
        existing.employee_id
        != employee.id
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=(
                "Leave request does not "
                "belong to current employee."
            ),
        )

    leave_request = await (
        service.cancel_request(
            request_id=request_id,
            actor_user_id=(
                scope.user_id
            ),
        )
    )

    await audit_leave_request_cancelled(
        control_session=(
            control_session
        ),
        workspace_id=(
            scope.workspace_id
        ),
        actor_user_id=(
            scope.user_id
        ),
        leave_request=(
            leave_request
        ),
    )

    return leave_request


# =========================================================
# MY BALANCES
# =========================================================


@router.get(
    "/me/balances",
    response_model=list[
        LeaveBalanceResponse
    ],
)
async def list_my_leave_balances(
    scope: TenantScope,
    balance_year: (
        int | None
    ) = Query(
        default=None,
        ge=2000,
        le=2200,
    ),
):
    employee = await (
        access_service(
            scope
        )
        .require_self_employee()
    )

    return await (
        LeaveService(
            scope.session
        )
        .repository
        .list_balances(
            employee_id=employee.id,
            balance_year=(
                balance_year
            ),
        )
    )


# =========================================================
# WORKSPACE / TEAM REQUEST QUEUE
# =========================================================


@router.get(
    "/requests",
    response_model=list[
        LeaveRequestResponse
    ],
)
async def list_leave_requests(
    scope: TenantScope,
    employee_id: (
        uuid.UUID | None
    ) = Query(
        default=None
    ),
    request_status: (
        LeaveRequestStatus | None
    ) = Query(
        default=None,
        alias="status",
    ),
    start_date: (
        date | None
    ) = Query(
        default=None
    ),
    end_date: (
        date | None
    ) = Query(
        default=None
    ),
):
    permissions = (
        permission_service(
            scope
        )
    )

    service = LeaveService(
        scope.session
    )

    if permissions.has(
        LEAVE_ALL_READ
    ):
        return await (
            service.repository
            .list_requests(
                employee_id=employee_id,
                status=request_status,
                start_date=start_date,
                end_date=end_date,
            )
        )

    permissions.require(
        LEAVE_TEAM_READ
    )

    if employee_id is None:
        raise HTTPException(
            status_code=(
                status
                .HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=(
                "employee_id is required "
                "for scoped leave reads."
            ),
        )

    await access_service(
        scope
    ).require_leave_read(
        employee_id=employee_id
    )

    return await (
        service.repository
        .list_requests(
            employee_id=employee_id,
            status=request_status,
            start_date=start_date,
            end_date=end_date,
        )
    )


# =========================================================
# APPROVAL
# =========================================================


@router.post(
    "/requests/{request_id}/approve",
    response_model=(
        LeaveRequestResponse
    ),
)
async def approve_leave_request(
    request_id: uuid.UUID,
    request: LeaveDecisionRequest,
    scope: TenantScope,
    control_session: ControlDB,
):
    service = LeaveService(
        scope.session
    )

    existing = await (
        service.repository
        .get_request(
            request_id
        )
    )

    if existing is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Leave request not found."
            ),
        )

    await access_service(
        scope
    ).require_leave_approval(
        employee_id=(
            existing.employee_id
        )
    )

    leave_request = await (
        service.approve_request(
            request_id=request_id,
            reviewer_user_id=(
                scope.user_id
            ),
            decision_note=(
                request.note
            ),
        )
    )

    await audit_leave_request_decision(
        control_session=(
            control_session
        ),
        workspace_id=(
            scope.workspace_id
        ),
        actor_user_id=(
            scope.user_id
        ),
        leave_request=(
            leave_request
        ),
        approved=True,
    )

    return leave_request


@router.post(
    "/requests/{request_id}/reject",
    response_model=(
        LeaveRequestResponse
    ),
)
async def reject_leave_request(
    request_id: uuid.UUID,
    request: LeaveDecisionRequest,
    scope: TenantScope,
    control_session: ControlDB,
):
    service = LeaveService(
        scope.session
    )

    existing = await (
        service.repository
        .get_request(
            request_id
        )
    )

    if existing is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Leave request not found."
            ),
        )

    await access_service(
        scope
    ).require_leave_approval(
        employee_id=(
            existing.employee_id
        )
    )

    leave_request = await (
        service.reject_request(
            request_id=request_id,
            reviewer_user_id=(
                scope.user_id
            ),
            decision_note=(
                request.note
            ),
        )
    )

    await audit_leave_request_decision(
        control_session=(
            control_session
        ),
        workspace_id=(
            scope.workspace_id
        ),
        actor_user_id=(
            scope.user_id
        ),
        leave_request=(
            leave_request
        ),
        approved=False,
    )

    return leave_request


# =========================================================
# EMPLOYEE BALANCES
# =========================================================


@router.get(
    "/employees/{employee_id}/balances",
    response_model=list[
        LeaveBalanceResponse
    ],
)
async def list_employee_leave_balances(
    employee_id: uuid.UUID,
    scope: TenantScope,
    balance_year: (
        int | None
    ) = Query(
        default=None,
        ge=2000,
        le=2200,
    ),
):
    await access_service(
        scope
    ).require_leave_read(
        employee_id=employee_id
    )

    return await (
        LeaveService(
            scope.session
        )
        .repository
        .list_balances(
            employee_id=employee_id,
            balance_year=(
                balance_year
            ),
        )
    )


@router.post(
    "/employees/{employee_id}"
    "/balances/{leave_type_id}"
    "/{balance_year}/adjustments",
    response_model=(
        LeaveBalanceResponse
    ),
)
async def adjust_employee_leave_balance(
    employee_id: uuid.UUID,
    leave_type_id: uuid.UUID,
    balance_year: int,
    request: (
        LeaveBalanceAdjustmentRequest
    ),
    scope: TenantScope,
    control_session: ControlDB,
):
    access = access_service(
        scope
    )

    access.require_balance_manage()

    await access.require_employee(
        employee_id
    )

    balance = await LeaveService(
        scope.session
    ).adjust_balance(
        employee_id=employee_id,
        leave_type_id=leave_type_id,
        balance_year=balance_year,
        actor_user_id=(
            scope.user_id
        ),
        request=request,
    )

    await audit_leave_balance_adjusted(
        control_session=(
            control_session
        ),
        workspace_id=(
            scope.workspace_id
        ),
        actor_user_id=(
            scope.user_id
        ),
        employee_id=employee_id,
        leave_type_id=(
            leave_type_id
        ),
        balance_id=balance.id,
        adjustment_days=(
            request.adjustment_days
        ),
        balance_year=(
            balance_year
        ),
    )

    return balance


__all__ = [
    "router",
]