from __future__ import annotations

import uuid
from datetime import (
    datetime,
    timezone,
)

from fastapi import (
    HTTPException,
    status,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.modules.employees.repository import (
    EmployeeRepository,
)
from app.modules.payroll.calculator import (
    PayrollCalculator,
)
from app.modules.payroll.lifecycle import (
    PayrollLifecycleError,
    PayrollRunLifecycle,
)
from app.modules.payroll.models import (
    CompensationContract,
    PayrollAdjustment,
    PayrollCalculation,
    PayrollCalculationStatus,
    PayrollRun,
    PayrollRunStatus,
)
from app.modules.payroll.repository import (
    PayrollRepository,
)
from app.modules.payroll.schemas import (
    CompensationContractCreateRequest,
    CompensationContractUpdateRequest,
    PayrollAdjustmentCreateRequest,
    PayrollCalculationInput,
    PayrollCalculationPreview,
    PayrollRunCreateRequest,
)


POLICY_VERSION = (
    "phase12.3-v1"
)


def utc_now() -> datetime:
    return datetime.now(
        timezone.utc
    )


class PayrollService:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

        self.repository = (
            PayrollRepository(
                session
            )
        )

        self.employees = (
            EmployeeRepository(
                session
            )
        )

    # =====================================================
    # HELPERS
    # =====================================================

    async def require_employee(
        self,
        employee_id: uuid.UUID,
    ):
        employee = await (
            self.employees
            .get_employee_by_id(
                employee_id
            )
        )

        if employee is None:
            raise HTTPException(
                status_code=(
                    status
                    .HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Employee not found."
                ),
            )

        return employee

    async def require_run(
        self,
        run_id: uuid.UUID,
    ) -> PayrollRun:
        run = await (
            self.repository
            .get_run(
                run_id
            )
        )

        if run is None:
            raise HTTPException(
                status_code=(
                    status
                    .HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Payroll run not found."
                ),
            )

        return run

    @staticmethod
    def require_mutable_run(
        run: PayrollRun,
    ) -> None:
        try:
            PayrollRunLifecycle.require_mutable(
                run
            )

        except PayrollLifecycleError as exc:
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=str(
                    exc
                ),
            ) from exc

    # =====================================================
    # COMPENSATION
    # =====================================================

    async def list_contracts(
        self,
        *,
        employee_id: (
            uuid.UUID | None
        ) = None,
        include_inactive: bool = False,
    ):
        return await (
            self.repository
            .list_contracts(
                employee_id=(
                    employee_id
                ),
                include_inactive=(
                    include_inactive
                ),
            )
        )

    async def get_contract(
        self,
        contract_id: uuid.UUID,
    ) -> CompensationContract:
        contract = await (
            self.repository
            .get_contract(
                contract_id
            )
        )

        if contract is None:
            raise HTTPException(
                status_code=(
                    status
                    .HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Compensation contract "
                    "not found."
                ),
            )

        return contract

    async def create_contract(
        self,
        request: (
            CompensationContractCreateRequest
        ),
        *,
        actor_user_id: uuid.UUID,
    ) -> CompensationContract:
        await self.require_employee(
            request.employee_id
        )

        overlap = await (
            self.repository
            .overlapping_contract_exists(
                employee_id=(
                    request.employee_id
                ),
                effective_from=(
                    request.effective_from
                ),
                effective_to=(
                    request.effective_to
                ),
            )
        )

        if overlap:
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "An active compensation "
                    "contract already overlaps "
                    "this effective period."
                ),
            )

        contract = (
            CompensationContract(
                employee_id=(
                    request.employee_id
                ),
                basis=(
                    request.basis
                ),
                base_amount=(
                    request.base_amount
                ),
                currency=(
                    request.currency
                ),
                effective_from=(
                    request.effective_from
                ),
                effective_to=(
                    request.effective_to
                ),
                standard_day_minutes=(
                    request
                    .standard_day_minutes
                ),
                monthly_divisor_days=(
                    request
                    .monthly_divisor_days
                ),
                overtime_multiplier=(
                    request
                    .overtime_multiplier
                ),
                overtime_enabled=(
                    request
                    .overtime_enabled
                ),
                notes=(
                    request.notes
                ),
                is_active=True,
                created_by_user_id=(
                    actor_user_id
                ),
            )
        )

        contract = await (
            self.repository
            .create_contract(
                contract
            )
        )

        await self.session.commit()

        return contract

    async def update_contract(
        self,
        contract_id: uuid.UUID,
        request: (
            CompensationContractUpdateRequest
        ),
    ) -> CompensationContract:
        contract = await (
            self.get_contract(
                contract_id
            )
        )

        update = (
            request.model_dump(
                exclude_unset=True
            )
        )

        proposed_end = (
            update.get(
                "effective_to",
                contract.effective_to,
            )
        )

        if (
            proposed_end is not None
            and proposed_end
            < contract.effective_from
        ):
            raise HTTPException(
                status_code=(
                    status
                    .HTTP_422_UNPROCESSABLE_ENTITY
                ),
                detail=(
                    "effective_to cannot be "
                    "before effective_from."
                ),
            )

        overlap = await (
            self.repository
            .overlapping_contract_exists(
                employee_id=(
                    contract.employee_id
                ),
                effective_from=(
                    contract.effective_from
                ),
                effective_to=(
                    proposed_end
                ),
                exclude_id=(
                    contract.id
                ),
            )
        )

        if overlap:
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Updated compensation "
                    "period overlaps another "
                    "active contract."
                ),
            )

        for field, value in (
            update.items()
        ):
            setattr(
                contract,
                field,
                value,
            )

        contract.updated_at = (
            utc_now()
        )

        await self.session.commit()

        await self.session.refresh(
            contract
        )

        return contract

    # =====================================================
    # RUNS
    # =====================================================

    async def list_runs(
        self,
    ):
        return await (
            self.repository
            .list_runs()
        )

    async def create_run(
        self,
        request: PayrollRunCreateRequest,
        *,
        actor_user_id: uuid.UUID,
    ) -> PayrollRun:
        run = PayrollRun(
            period_start=(
                request.period_start
            ),
            period_end=(
                request.period_end
            ),
            cutoff_date=(
                request.cutoff_date
            ),
            currency=(
                request.currency
            ),
            status=(
                PayrollRunStatus.DRAFT
            ),
            policy_version=(
                POLICY_VERSION
            ),
            notes=(
                request.notes
            ),
            created_by_user_id=(
                actor_user_id
            ),
        )

        run = await (
            self.repository
            .create_run(
                run
            )
        )

        await self.session.commit()

        return run

    async def list_calculations(
        self,
        *,
        run_id: uuid.UUID,
    ):
        await self.require_run(
            run_id
        )

        return await (
            self.repository
            .list_calculations(
                run_id=run_id
            )
        )

    # =====================================================
    # PURE CALCULATOR
    # =====================================================

    def preview(
        self,
        request: PayrollCalculationInput,
    ) -> PayrollCalculationPreview:
        return (
            PayrollCalculator
            .calculate(
                request
            )
        )

    # =====================================================
    # INTERNAL AUTHORITATIVE SNAPSHOT
    # =====================================================

    async def persist_calculation(
        self,
        *,
        run_id: uuid.UUID,
        request: PayrollCalculationInput,
        actor_user_id: uuid.UUID,
        source_snapshot: dict,
    ) -> PayrollCalculation:
        run = await self.require_run(
            run_id
        )

        self.require_mutable_run(
            run
        )

        await self.require_employee(
            request.employee_id
        )

        contract = await (
            self.repository
            .get_contract(
                request
                .compensation_contract_id
            )
        )

        if (
            contract is None
            or contract.employee_id
            != request.employee_id
        ):
            raise HTTPException(
                status_code=(
                    status
                    .HTTP_422_UNPROCESSABLE_ENTITY
                ),
                detail=(
                    "Compensation contract "
                    "does not belong to the "
                    "employee."
                ),
            )

        if (
            contract.currency
            != run.currency
        ):
            raise HTTPException(
                status_code=(
                    status
                    .HTTP_422_UNPROCESSABLE_ENTITY
                ),
                detail=(
                    "Compensation currency "
                    "does not match payroll "
                    "run currency."
                ),
            )

        preview = (
            PayrollCalculator
            .calculate(
                request
            )
        )

        calculation = (
            PayrollCalculation(
                payroll_run_id=(
                    run.id
                ),
                employee_id=(
                    request.employee_id
                ),
                compensation_contract_id=(
                    contract.id
                ),
                status=(
                    PayrollCalculationStatus
                    .CALCULATED
                ),
                currency=(
                    preview.currency
                ),
                base_amount=(
                    request.base_amount
                ),
                daily_rate=(
                    preview.daily_rate
                ),
                hourly_rate=(
                    preview.hourly_rate
                ),
                minute_rate=(
                    preview.minute_rate
                ),
                scheduled_minutes=(
                    preview
                    .scheduled_minutes
                ),
                payable_minutes=(
                    preview
                    .payable_minutes
                ),
                paid_leave_minutes=(
                    preview
                    .paid_leave_minutes
                ),
                unpaid_leave_minutes=(
                    preview
                    .unpaid_leave_minutes
                ),
                overtime_minutes=(
                    preview
                    .overtime_minutes
                ),
                base_pay=(
                    preview.base_pay
                ),
                overtime_pay=(
                    preview.overtime_pay
                ),
                additions_total=(
                    preview
                    .additions_total
                ),
                deductions_total=(
                    preview
                    .deductions_total
                ),
                gross_pay=(
                    preview.gross_pay
                ),
                net_pay=(
                    preview.net_pay
                ),
                source_snapshot=(
                    source_snapshot
                ),
                explanation_snapshot={
                    "basis": (
                        request
                        .basis.value
                    ),
                    "scheduled_minutes": (
                        preview
                        .scheduled_minutes
                    ),
                    "payable_minutes": (
                        preview
                        .payable_minutes
                    ),
                    "paid_leave_minutes": (
                        preview
                        .paid_leave_minutes
                    ),
                    "unpaid_leave_minutes": (
                        preview
                        .unpaid_leave_minutes
                    ),
                    "overtime_minutes": (
                        preview
                        .overtime_minutes
                    ),
                    "daily_rate": str(
                        preview.daily_rate
                    ),
                    "hourly_rate": str(
                        preview.hourly_rate
                    ),
                    "minute_rate": str(
                        preview.minute_rate
                    ),
                },
                policy_version=(
                    run.policy_version
                ),
                calculated_by_user_id=(
                    actor_user_id
                ),
                calculated_at=(
                    utc_now()
                ),
            )
        )

        calculation = await (
            self.repository
            .upsert_calculation(
                calculation
            )
        )

        try:
            PayrollRunLifecycle.move_to_review(
                run
            )

        except PayrollLifecycleError as exc:
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=str(
                    exc
                ),
            ) from exc

        await self.session.commit()

        return calculation

    # =====================================================
    # ADJUSTMENTS
    # =====================================================

    async def add_adjustment(
        self,
        *,
        run_id: uuid.UUID,
        request: (
            PayrollAdjustmentCreateRequest
        ),
        actor_user_id: uuid.UUID,
    ) -> PayrollAdjustment:
        run = await self.require_run(
            run_id
        )

        self.require_mutable_run(
            run
        )

        await self.require_employee(
            request.employee_id
        )

        adjustment = (
            PayrollAdjustment(
                payroll_run_id=(
                    run.id
                ),
                employee_id=(
                    request.employee_id
                ),
                adjustment_type=(
                    request.adjustment_type
                ),
                amount=(
                    request.amount
                ),
                reason=(
                    request
                    .reason
                    .strip()
                ),
                created_by_user_id=(
                    actor_user_id
                ),
            )
        )

        adjustment = await (
            self.repository
            .create_adjustment(
                adjustment
            )
        )

        await self.session.commit()

        return adjustment

    # =====================================================
    # APPROVE
    # =====================================================

    async def approve_run(
        self,
        *,
        run_id: uuid.UUID,
        actor_user_id: uuid.UUID,
    ) -> PayrollRun:
        run = await self.require_run(
            run_id
        )

        calculations = await (
            self.repository
            .list_calculations(
                run_id=run.id
            )
        )

        if not calculations:
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Payroll run cannot be "
                    "approved before calculation."
                ),
            )

        try:
            PayrollRunLifecycle.approve(
                run,
                actor_user_id=(
                    actor_user_id
                ),
            )

        except PayrollLifecycleError as exc:
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=str(
                    exc
                ),
            ) from exc

        await self.session.commit()

        await self.session.refresh(
            run
        )

        return run

    # =====================================================
    # LOCK
    # =====================================================

    async def lock_run(
        self,
        *,
        run_id: uuid.UUID,
        actor_user_id: uuid.UUID,
    ) -> PayrollRun:
        run = await self.require_run(
            run_id
        )

        try:
            PayrollRunLifecycle.lock(
                run,
                actor_user_id=(
                    actor_user_id
                ),
            )

        except PayrollLifecycleError as exc:
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=str(
                    exc
                ),
            ) from exc

        await self.session.commit()

        await self.session.refresh(
            run
        )

        return run

    # =====================================================
    # PAID
    # =====================================================

    async def mark_run_paid(
        self,
        *,
        run_id: uuid.UUID,
        actor_user_id: uuid.UUID,
    ) -> PayrollRun:
        run = await self.require_run(
            run_id
        )

        try:
            PayrollRunLifecycle.mark_paid(
                run,
                actor_user_id=(
                    actor_user_id
                ),
            )

        except PayrollLifecycleError as exc:
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=str(
                    exc
                ),
            ) from exc

        await self.session.commit()

        await self.session.refresh(
            run
        )

        return run


__all__ = [
    "POLICY_VERSION",
    "PayrollService",
]