from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from fastapi import (
    HTTPException,
    status,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.modules.payroll.attendance_source import (
    PayrollAttendanceSourceService,
)
from app.modules.payroll.models import (
    CompensationContract,
    PayrollAdjustmentType,
)
from app.modules.payroll.repository import (
    PayrollRepository,
)
from app.modules.payroll.schedule_source import (
    PayrollScheduleSourceService,
)
from app.modules.payroll.leave_source import (
    PayrollLeaveSourceService,
)
from app.modules.payroll.source_schemas import (
    PayrollAdjustmentSource,
    PayrollEmployeeSourceBundle,
)


class PayrollSourceAssembler:
    """
    Assemble all authoritative server-side Payroll inputs.
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.repository = (
            PayrollRepository(
                session
            )
        )

        self.schedule = (
            PayrollScheduleSourceService(
                session
            )
        )

        self.attendance = (
            PayrollAttendanceSourceService(
                session
            )
        )

        self.leave = (
            PayrollLeaveSourceService(
                session
            )
        )

    async def require_contract(
        self,
        *,
        employee_id: uuid.UUID,
        period_start: date,
        period_end: date,
    ) -> CompensationContract:
        contract = await (
            self.repository
            .get_active_contract_for_date(
                employee_id=(
                    employee_id
                ),
                contract_date=(
                    period_end
                ),
            )
        )

        if contract is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Employee has no active "
                    "compensation contract for "
                    "this payroll period."
                ),
            )

        # Do not silently use one contract that only covers
        # part of the payroll period.
        if (
            contract.effective_from
            > period_start
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Compensation contract does "
                    "not cover the full payroll "
                    "period."
                ),
            )

        if (
            contract.effective_to
            is not None
            and contract.effective_to
            < period_end
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Compensation contract does "
                    "not cover the full payroll "
                    "period."
                ),
            )

        return contract

    async def adjustments(
        self,
        *,
        run_id: uuid.UUID,
        employee_id: uuid.UUID,
    ) -> PayrollAdjustmentSource:
        rows = await (
            self.repository
            .list_adjustments(
                run_id=run_id,
                employee_id=(
                    employee_id
                ),
            )
        )

        additions = Decimal(
            "0"
        )

        deductions = Decimal(
            "0"
        )

        ids: list[
            uuid.UUID
        ] = []

        for row in rows:
            ids.append(
                row.id
            )

            if (
                row.adjustment_type
                == (
                    PayrollAdjustmentType
                    .ADDITION
                )
            ):
                additions += row.amount

            else:
                deductions += row.amount

        return PayrollAdjustmentSource(
            employee_id=employee_id,
            additions_total=(
                additions
            ),
            deductions_total=(
                deductions
            ),
            adjustment_ids=ids,
        )

    async def assemble(
        self,
        *,
        run_id: uuid.UUID,
        employee_id: uuid.UUID,
        period_start: date,
        period_end: date,
    ) -> tuple[
        CompensationContract,
        PayrollEmployeeSourceBundle,
    ]:
        contract = await (
            self.require_contract(
                employee_id=employee_id,
                period_start=(
                    period_start
                ),
                period_end=(
                    period_end
                ),
            )
        )

        schedule = await (
            self.schedule.resolve(
                employee_id=employee_id,
                period_start=(
                    period_start
                ),
                period_end=(
                    period_end
                ),
            )
        )

        attendance = await (
            self.attendance.resolve(
                employee_id=employee_id,
                period_start=(
                    period_start
                ),
                period_end=(
                    period_end
                ),
            )
        )

        leave = await (
            self.leave.resolve(
                employee_id=employee_id,
                period_start=(
                    period_start
                ),
                period_end=(
                    period_end
                ),
                schedule=schedule,
            )
        )

        adjustments = await (
            self.adjustments(
                run_id=run_id,
                employee_id=(
                    employee_id
                ),
            )
        )

        bundle = (
            PayrollEmployeeSourceBundle(
                employee_id=(
                    employee_id
                ),
                compensation_contract_id=(
                    contract.id
                ),
                schedule=schedule,
                attendance=attendance,
                leave=leave,
                adjustments=(
                    adjustments
                ),
            )
        )

        return (
            contract,
            bundle,
        )


__all__ = [
    "PayrollSourceAssembler",
]