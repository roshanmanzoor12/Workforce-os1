from __future__ import annotations

import uuid
from collections.abc import (
    Sequence,
)
from datetime import date

from sqlalchemy import (
    or_,
    select,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.modules.payroll.models import (
    CompensationContract,
    PayrollAdjustment,
    PayrollCalculation,
    PayrollRun,
)


# =========================================================
# PAYROLL REPOSITORY
# =========================================================


class PayrollRepository:
    """
    Tenant-scoped persistence layer for Payroll.

    Security boundary:

    - this repository never resolves a workspace
    - this repository never accepts database_name
    - this repository never creates a tenant session
    - caller must supply an already-authorized tenant AsyncSession

    HTTP authorization and target scope belong outside this layer.
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    # =====================================================
    # COMPENSATION CONTRACTS
    # =====================================================

    async def create_contract(
        self,
        contract: CompensationContract,
    ) -> CompensationContract:
        self.session.add(
            contract
        )

        await self.session.flush()

        await self.session.refresh(
            contract
        )

        return contract

    async def get_contract(
        self,
        contract_id: uuid.UUID,
    ) -> CompensationContract | None:
        result = await (
            self.session.execute(
                select(
                    CompensationContract
                ).where(
                    CompensationContract.id
                    == contract_id
                )
            )
        )

        return (
            result
            .scalar_one_or_none()
        )

    async def list_contracts(
        self,
        *,
        employee_id: (
            uuid.UUID | None
        ) = None,
        include_inactive: bool = False,
    ) -> Sequence[
        CompensationContract
    ]:
        statement = select(
            CompensationContract
        )

        if employee_id is not None:
            statement = (
                statement.where(
                    CompensationContract
                    .employee_id
                    == employee_id
                )
            )

        if not include_inactive:
            statement = (
                statement.where(
                    CompensationContract
                    .is_active
                    .is_(
                        True
                    )
                )
            )

        statement = (
            statement.order_by(
                CompensationContract
                .effective_from
                .desc(),

                CompensationContract
                .created_at
                .desc(),
            )
        )

        result = await (
            self.session.execute(
                statement
            )
        )

        return (
            result
            .scalars()
            .all()
        )

    async def get_active_contract_for_date(
        self,
        *,
        employee_id: uuid.UUID,
        contract_date: date,
    ) -> CompensationContract | None:
        """
        Resolve the most recent active compensation contract
        effective on one date.
        """

        statement = (
            select(
                CompensationContract
            )
            .where(
                CompensationContract
                .employee_id
                == employee_id,

                CompensationContract
                .is_active
                .is_(
                    True
                ),

                CompensationContract
                .effective_from
                <= contract_date,

                or_(
                    CompensationContract
                    .effective_to
                    .is_(
                        None
                    ),

                    CompensationContract
                    .effective_to
                    >= contract_date,
                ),
            )
            .order_by(
                CompensationContract
                .effective_from
                .desc(),

                CompensationContract
                .created_at
                .desc(),
            )
            .limit(
                1
            )
        )

        result = await (
            self.session.execute(
                statement
            )
        )

        return (
            result
            .scalar_one_or_none()
        )

    async def overlapping_contract_exists(
        self,
        *,
        employee_id: uuid.UUID,
        effective_from: date,
        effective_to: (
            date | None
        ),
        exclude_id: (
            uuid.UUID | None
        ) = None,
    ) -> bool:
        """
        Return True when another active compensation contract
        overlaps the requested date interval.

        Open-ended effective_to is treated as date.max.
        """

        requested_end = (
            effective_to
            or date.max
        )

        statement = (
            select(
                CompensationContract.id
            )
            .where(
                CompensationContract
                .employee_id
                == employee_id,

                CompensationContract
                .is_active
                .is_(
                    True
                ),

                CompensationContract
                .effective_from
                <= requested_end,

                or_(
                    CompensationContract
                    .effective_to
                    .is_(
                        None
                    ),

                    CompensationContract
                    .effective_to
                    >= effective_from,
                ),
            )
            .limit(
                1
            )
        )

        if exclude_id is not None:
            statement = (
                statement.where(
                    CompensationContract.id
                    != exclude_id
                )
            )

        result = await (
            self.session.execute(
                statement
            )
        )

        return (
            result
            .scalar_one_or_none()
            is not None
        )

    # =====================================================
    # PAYROLL RUNS
    # =====================================================

    async def create_run(
        self,
        run: PayrollRun,
    ) -> PayrollRun:
        self.session.add(
            run
        )

        await self.session.flush()

        await self.session.refresh(
            run
        )

        return run

    async def get_run(
        self,
        run_id: uuid.UUID,
    ) -> PayrollRun | None:
        result = await (
            self.session.execute(
                select(
                    PayrollRun
                ).where(
                    PayrollRun.id
                    == run_id
                )
            )
        )

        return (
            result
            .scalar_one_or_none()
        )

    async def list_runs(
        self,
    ) -> Sequence[
        PayrollRun
    ]:
        result = await (
            self.session.execute(
                select(
                    PayrollRun
                )
                .order_by(
                    PayrollRun
                    .period_start
                    .desc(),

                    PayrollRun
                    .created_at
                    .desc(),
                )
            )
        )

        return (
            result
            .scalars()
            .all()
        )

    # =====================================================
    # CALCULATIONS
    # =====================================================

    async def get_calculation(
        self,
        *,
        run_id: uuid.UUID,
        employee_id: uuid.UUID,
    ) -> PayrollCalculation | None:
        result = await (
            self.session.execute(
                select(
                    PayrollCalculation
                ).where(
                    PayrollCalculation
                    .payroll_run_id
                    == run_id,

                    PayrollCalculation
                    .employee_id
                    == employee_id,
                )
            )
        )

        return (
            result
            .scalar_one_or_none()
        )

    async def list_calculations(
        self,
        *,
        run_id: uuid.UUID,
    ) -> Sequence[
        PayrollCalculation
    ]:
        result = await (
            self.session.execute(
                select(
                    PayrollCalculation
                )
                .where(
                    PayrollCalculation
                    .payroll_run_id
                    == run_id
                )
                .order_by(
                    PayrollCalculation
                    .employee_id
                    .asc()
                )
            )
        )

        return (
            result
            .scalars()
            .all()
        )

    async def upsert_calculation(
        self,
        calculation: PayrollCalculation,
    ) -> PayrollCalculation:
        """
        Insert or replace the mutable draft/review calculation
        snapshot for one run + employee.

        Lock enforcement belongs to PayrollService. Repository does
        not independently decide whether a run is mutable.
        """

        existing = await (
            self.get_calculation(
                run_id=(
                    calculation
                    .payroll_run_id
                ),
                employee_id=(
                    calculation
                    .employee_id
                ),
            )
        )

        if existing is None:
            self.session.add(
                calculation
            )

            target = calculation

        else:
            existing.compensation_contract_id = (
                calculation
                .compensation_contract_id
            )

            existing.status = (
                calculation.status
            )

            existing.currency = (
                calculation.currency
            )

            existing.base_amount = (
                calculation.base_amount
            )

            existing.daily_rate = (
                calculation.daily_rate
            )

            existing.hourly_rate = (
                calculation.hourly_rate
            )

            existing.minute_rate = (
                calculation.minute_rate
            )

            existing.scheduled_minutes = (
                calculation
                .scheduled_minutes
            )

            existing.payable_minutes = (
                calculation
                .payable_minutes
            )

            existing.paid_leave_minutes = (
                calculation
                .paid_leave_minutes
            )

            existing.unpaid_leave_minutes = (
                calculation
                .unpaid_leave_minutes
            )

            existing.overtime_minutes = (
                calculation
                .overtime_minutes
            )

            existing.base_pay = (
                calculation.base_pay
            )

            existing.overtime_pay = (
                calculation.overtime_pay
            )

            existing.additions_total = (
                calculation
                .additions_total
            )

            existing.deductions_total = (
                calculation
                .deductions_total
            )

            existing.gross_pay = (
                calculation.gross_pay
            )

            existing.net_pay = (
                calculation.net_pay
            )

            existing.source_snapshot = (
                calculation
                .source_snapshot
            )

            existing.explanation_snapshot = (
                calculation
                .explanation_snapshot
            )

            existing.policy_version = (
                calculation
                .policy_version
            )

            existing.calculated_by_user_id = (
                calculation
                .calculated_by_user_id
            )

            existing.calculated_at = (
                calculation
                .calculated_at
            )

            target = existing

        await self.session.flush()

        await self.session.refresh(
            target
        )

        return target

    # =====================================================
    # ADJUSTMENTS
    # =====================================================

    async def create_adjustment(
        self,
        adjustment: PayrollAdjustment,
    ) -> PayrollAdjustment:
        self.session.add(
            adjustment
        )

        await self.session.flush()

        await self.session.refresh(
            adjustment
        )

        return adjustment

    async def get_adjustment(
        self,
        adjustment_id: uuid.UUID,
    ) -> PayrollAdjustment | None:
        result = await (
            self.session.execute(
                select(
                    PayrollAdjustment
                ).where(
                    PayrollAdjustment.id
                    == adjustment_id
                )
            )
        )

        return (
            result
            .scalar_one_or_none()
        )

    async def list_adjustments(
        self,
        *,
        run_id: uuid.UUID,
        employee_id: (
            uuid.UUID | None
        ) = None,
    ) -> Sequence[
        PayrollAdjustment
    ]:
        statement = (
            select(
                PayrollAdjustment
            )
            .where(
                PayrollAdjustment
                .payroll_run_id
                == run_id
            )
        )

        if employee_id is not None:
            statement = (
                statement.where(
                    PayrollAdjustment
                    .employee_id
                    == employee_id
                )
            )

        statement = (
            statement.order_by(
                PayrollAdjustment
                .created_at
                .asc(),

                PayrollAdjustment.id
                .asc(),
            )
        )

        result = await (
            self.session.execute(
                statement
            )
        )

        return (
            result
            .scalars()
            .all()
        )


# =========================================================
# FACTORY
# =========================================================


def get_payroll_repository(
    session: AsyncSession,
) -> PayrollRepository:
    return PayrollRepository(
        session
    )


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "PayrollRepository",
    "get_payroll_repository",
]