from __future__ import annotations

import uuid

from fastapi import (
    APIRouter,
    Query,
    status,
)

from app.db.tenant_dependency import (
    ControlDB,
    TenantScope,
)
from app.modules.payroll.access_service import (
    PayrollAccessService,
)
from app.modules.payroll.audit import (
    PayrollAuditService,
)
from app.modules.payroll.calculation_service import (
    PayrollCalculationService,
)
from app.modules.payroll.read_service import (
    PayrollReadService,
)
from app.modules.payroll.schemas import (
    CompensationContractCreateRequest,
    CompensationContractResponse,
    CompensationContractUpdateRequest,
    PayrollAdjustmentCreateRequest,
    PayrollAdjustmentResponse,
    PayrollCalculationResponse,
    PayrollRunCreateRequest,
    PayrollRunResponse,
)
from app.modules.payroll.service import (
    PayrollService,
)
from app.modules.payroll.source_schemas import (
    PayrollCalculateRequest,
    PayrollRunCalculationResponse,
)
from app.modules.payroll.summary_schemas import (
    PayrollRunSummaryResponse,
)


router = APIRouter(
    prefix=(
        "/workspaces/{workspace_id}"
    ),
    tags=[
        "Payroll",
    ],
)


def access(
    scope: TenantScope,
) -> PayrollAccessService:
    return PayrollAccessService(
        scope=scope,
        session=scope.session,
    )


def service(
    scope: TenantScope,
) -> PayrollService:
    return PayrollService(
        scope.session
    )


def reader(
    scope: TenantScope,
) -> PayrollReadService:
    return PayrollReadService(
        scope.session
    )


def auditor(
    control_session: ControlDB,
) -> PayrollAuditService:
    return PayrollAuditService(
        control_session
    )


# =========================================================
# COMPENSATION
# =========================================================


@router.get(
    "/compensation/contracts",
    response_model=list[
        CompensationContractResponse
    ],
)
async def list_compensation_contracts(
    scope: TenantScope,
    employee_id: (
        uuid.UUID | None
    ) = Query(
        default=None
    ),
    include_inactive: bool = Query(
        default=False
    ),
):
    payroll_access = access(
        scope
    )

    if employee_id is None:
        payroll_access.require_payroll_read()

    else:
        await (
            payroll_access
            .require_employee_compensation_read(
                employee_id
            )
        )

    return await (
        service(
            scope
        )
        .list_contracts(
            employee_id=employee_id,
            include_inactive=(
                include_inactive
            ),
        )
    )


@router.post(
    "/compensation/contracts",
    response_model=(
        CompensationContractResponse
    ),
    status_code=(
        status.HTTP_201_CREATED
    ),
)
async def create_compensation_contract(
    request: (
        CompensationContractCreateRequest
    ),
    scope: TenantScope,
    control_session: ControlDB,
):
    access(
        scope
    ).require_payroll_manage()

    contract = await (
        service(
            scope
        )
        .create_contract(
            request,
            actor_user_id=(
                scope.user_id
            ),
        )
    )

    await auditor(
        control_session
    ).compensation_created(
        workspace_id=(
            scope.workspace_id
        ),
        actor_user_id=(
            scope.user_id
        ),
        contract_id=contract.id,
        employee_id=(
            contract.employee_id
        ),
    )

    return contract


@router.get(
    (
        "/compensation/contracts/"
        "{contract_id}"
    ),
    response_model=(
        CompensationContractResponse
    ),
)
async def get_compensation_contract(
    contract_id: uuid.UUID,
    scope: TenantScope,
):
    return await (
        access(
            scope
        )
        .require_contract_read(
            contract_id
        )
    )


@router.patch(
    (
        "/compensation/contracts/"
        "{contract_id}"
    ),
    response_model=(
        CompensationContractResponse
    ),
)
async def update_compensation_contract(
    contract_id: uuid.UUID,
    request: (
        CompensationContractUpdateRequest
    ),
    scope: TenantScope,
    control_session: ControlDB,
):
    access(
        scope
    ).require_payroll_manage()

    contract = await (
        service(
            scope
        )
        .update_contract(
            contract_id,
            request,
        )
    )

    await auditor(
        control_session
    ).compensation_updated(
        workspace_id=(
            scope.workspace_id
        ),
        actor_user_id=(
            scope.user_id
        ),
        contract_id=contract.id,
        employee_id=(
            contract.employee_id
        ),
    )

    return contract


# =========================================================
# RUNS
# =========================================================


@router.get(
    "/payroll/runs",
    response_model=list[
        PayrollRunResponse
    ],
)
async def list_payroll_runs(
    scope: TenantScope,
):
    access(
        scope
    ).require_payroll_read()

    return await (
        service(
            scope
        )
        .list_runs()
    )


@router.post(
    "/payroll/runs",
    response_model=(
        PayrollRunResponse
    ),
    status_code=(
        status.HTTP_201_CREATED
    ),
)
async def create_payroll_run(
    request: PayrollRunCreateRequest,
    scope: TenantScope,
    control_session: ControlDB,
):
    access(
        scope
    ).require_payroll_manage()

    run = await (
        service(
            scope
        )
        .create_run(
            request,
            actor_user_id=(
                scope.user_id
            ),
        )
    )

    await auditor(
        control_session
    ).run_created(
        workspace_id=(
            scope.workspace_id
        ),
        actor_user_id=(
            scope.user_id
        ),
        run_id=run.id,
    )

    return run


@router.get(
    "/payroll/runs/{run_id}",
    response_model=(
        PayrollRunResponse
    ),
)
async def get_payroll_run(
    run_id: uuid.UUID,
    scope: TenantScope,
):
    access(
        scope
    ).require_payroll_read()

    return await (
        reader(
            scope
        )
        .get_run(
            run_id
        )
    )


# =========================================================
# AUTHORITATIVE CALCULATION
# =========================================================


@router.post(
    (
        "/payroll/runs/{run_id}"
        "/calculate"
    ),
    response_model=(
        PayrollRunCalculationResponse
    ),
)
async def calculate_payroll_run(
    run_id: uuid.UUID,
    request: PayrollCalculateRequest,
    scope: TenantScope,
    control_session: ControlDB,
):
    access(
        scope
    ).require_payroll_manage()

    result = await (
        PayrollCalculationService(
            scope.session
        )
        .calculate_run(
            run_id=run_id,
            request=request,
            actor_user_id=(
                scope.user_id
            ),
        )
    )

    await auditor(
        control_session
    ).run_calculated(
        workspace_id=(
            scope.workspace_id
        ),
        actor_user_id=(
            scope.user_id
        ),
        run_id=run_id,
        processed_employees=(
            result.processed_employees
        ),
        skipped_employees=(
            result.skipped_employees
        ),
    )

    return result


# =========================================================
# SUMMARY / ROWS
# =========================================================


@router.get(
    (
        "/payroll/runs/{run_id}"
        "/summary"
    ),
    response_model=(
        PayrollRunSummaryResponse
    ),
)
async def get_payroll_run_summary(
    run_id: uuid.UUID,
    scope: TenantScope,
):
    access(
        scope
    ).require_payroll_read()

    return await (
        reader(
            scope
        )
        .summary(
            run_id=run_id
        )
    )


@router.get(
    (
        "/payroll/runs/{run_id}"
        "/employees"
    ),
    response_model=list[
        PayrollCalculationResponse
    ],
)
async def list_payroll_run_employees(
    run_id: uuid.UUID,
    scope: TenantScope,
):
    access(
        scope
    ).require_payroll_read()

    return await (
        service(
            scope
        )
        .list_calculations(
            run_id=run_id
        )
    )


# =========================================================
# ADJUSTMENTS
# =========================================================


@router.post(
    (
        "/payroll/runs/{run_id}"
        "/adjustments"
    ),
    response_model=(
        PayrollAdjustmentResponse
    ),
    status_code=(
        status.HTTP_201_CREATED
    ),
)
async def add_payroll_adjustment(
    run_id: uuid.UUID,
    request: (
        PayrollAdjustmentCreateRequest
    ),
    scope: TenantScope,
    control_session: ControlDB,
):
    access(
        scope
    ).require_payroll_manage()

    adjustment = await (
        service(
            scope
        )
        .add_adjustment(
            run_id=run_id,
            request=request,
            actor_user_id=(
                scope.user_id
            ),
        )
    )

    await auditor(
        control_session
    ).adjustment_created(
        workspace_id=(
            scope.workspace_id
        ),
        actor_user_id=(
            scope.user_id
        ),
        adjustment_id=(
            adjustment.id
        ),
        run_id=(
            adjustment.payroll_run_id
        ),
        employee_id=(
            adjustment.employee_id
        ),
    )

    return adjustment


# =========================================================
# STATE TRANSITIONS
# =========================================================


@router.post(
    (
        "/payroll/runs/{run_id}"
        "/approve"
    ),
    response_model=(
        PayrollRunResponse
    ),
)
async def approve_payroll_run(
    run_id: uuid.UUID,
    scope: TenantScope,
    control_session: ControlDB,
):
    access(
        scope
    ).require_payroll_manage()

    run = await (
        service(
            scope
        )
        .approve_run(
            run_id=run_id,
            actor_user_id=(
                scope.user_id
            ),
        )
    )

    await auditor(
        control_session
    ).run_approved(
        workspace_id=(
            scope.workspace_id
        ),
        actor_user_id=(
            scope.user_id
        ),
        run_id=run.id,
    )

    return run


@router.post(
    (
        "/payroll/runs/{run_id}"
        "/lock"
    ),
    response_model=(
        PayrollRunResponse
    ),
)
async def lock_payroll_run(
    run_id: uuid.UUID,
    scope: TenantScope,
    control_session: ControlDB,
):
    access(
        scope
    ).require_payroll_manage()

    run = await (
        service(
            scope
        )
        .lock_run(
            run_id=run_id,
            actor_user_id=(
                scope.user_id
            ),
        )
    )

    await auditor(
        control_session
    ).run_locked(
        workspace_id=(
            scope.workspace_id
        ),
        actor_user_id=(
            scope.user_id
        ),
        run_id=run.id,
    )

    return run


@router.post(
    (
        "/payroll/runs/{run_id}"
        "/mark-paid"
    ),
    response_model=(
        PayrollRunResponse
    ),
)
async def mark_payroll_run_paid(
    run_id: uuid.UUID,
    scope: TenantScope,
    control_session: ControlDB,
):
    access(
        scope
    ).require_payroll_manage()

    run = await (
        service(
            scope
        )
        .mark_run_paid(
            run_id=run_id,
            actor_user_id=(
                scope.user_id
            ),
        )
    )

    await auditor(
        control_session
    ).run_paid(
        workspace_id=(
            scope.workspace_id
        ),
        actor_user_id=(
            scope.user_id
        ),
        run_id=run.id,
    )

    return run


__all__ = [
    "router",
]