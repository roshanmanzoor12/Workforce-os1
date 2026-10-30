from __future__ import annotations

import uuid

from fastapi import (
    APIRouter,
    status,
)

from app.db.tenant_dependency import (
    TenantScope,
)
from app.modules.payroll.payslip_access import (
    PayrollPayslipAccessService,
)
from app.modules.payroll.payslip_schemas import (
    PayrollPayslipDetailResponse,
    PayrollPayslipPublishResponse,
    PayrollPayslipSummaryResponse,
)
from app.modules.payroll.payslip_service import (
    PayrollPayslipService,
)
from app.modules.workspace_permissions.permissions import (
    WorkspacePermission,
)
from app.modules.workspace_permissions.service import (
    WorkspacePermissionService,
)


router = APIRouter(
    prefix=(
        "/workspaces/{workspace_id}"
        "/payroll"
    ),
    tags=[
        "Payroll Payslips",
    ],
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
) -> PayrollPayslipAccessService:
    return (
        PayrollPayslipAccessService(
            scope=scope,
            session=scope.session,
        )
    )


def payslip_service(
    scope: TenantScope,
) -> PayrollPayslipService:
    return PayrollPayslipService(
        scope.session
    )


# =========================================================
# SELF PAYSLIPS
# =========================================================


@router.get(
    "/me/payslips",
    response_model=list[
        PayrollPayslipSummaryResponse
    ],
)
async def list_my_payslips(
    scope: TenantScope,
):
    permission_service(
        scope
    ).require(
        WorkspacePermission
        .COMPENSATION_SELF_READ
        .value
    )

    employee = await (
        access_service(
            scope
        )
        .require_self_employee()
    )

    return await (
        payslip_service(
            scope
        )
        .list_employee_payslips(
            employee_id=(
                employee.id
            )
        )
    )


# =========================================================
# PAYSLIP DETAIL
# =========================================================


@router.get(
    "/payslips/{payslip_id}",
    response_model=(
        PayrollPayslipDetailResponse
    ),
)
async def get_payslip(
    payslip_id: uuid.UUID,
    scope: TenantScope,
):
    return await (
        access_service(
            scope
        )
        .require_read(
            payslip_id
        )
    )


# =========================================================
# PUBLISH RUN PAYSLIPS
# =========================================================


@router.post(
    (
        "/runs/{run_id}"
        "/payslips/publish"
    ),
    response_model=(
        PayrollPayslipPublishResponse
    ),
    status_code=(
        status.HTTP_200_OK
    ),
)
async def publish_run_payslips(
    run_id: uuid.UUID,
    scope: TenantScope,
):
    permission_service(
        scope
    ).require(
        WorkspacePermission
        .PAYROLL_MANAGE
        .value
    )

    return await (
        payslip_service(
            scope
        )
        .publish_run(
            run_id=run_id,
            actor_user_id=(
                scope.user_id
            ),
        )
    )


__all__ = [
    "router",
]
