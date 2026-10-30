from __future__ import annotations

from collections.abc import (
    Iterable,
)
from decimal import Decimal

from app.modules.payroll.models import (
    PayrollCalculation,
    PayrollRun,
)
from app.modules.payroll.summary_schemas import (
    PayrollRunSummaryResponse,
)


ZERO = Decimal(
    "0"
)


class PayrollSummaryBuilder:
    @staticmethod
    def build(
        *,
        run: PayrollRun,
        calculations: Iterable[
            PayrollCalculation
        ],
    ) -> PayrollRunSummaryResponse:
        rows = list(
            calculations
        )

        return PayrollRunSummaryResponse(
            run_id=run.id,
            status=run.status,
            currency=run.currency,
            employees=len(
                rows
            ),
            scheduled_minutes=sum(
                int(
                    row.scheduled_minutes
                )
                for row in rows
            ),
            payable_minutes=sum(
                int(
                    row.payable_minutes
                )
                for row in rows
            ),
            paid_leave_minutes=sum(
                int(
                    row.paid_leave_minutes
                )
                for row in rows
            ),
            unpaid_leave_minutes=sum(
                int(
                    row.unpaid_leave_minutes
                )
                for row in rows
            ),
            overtime_minutes=sum(
                int(
                    row.overtime_minutes
                )
                for row in rows
            ),
            base_pay=sum(
                (
                    row.base_pay
                    for row in rows
                ),
                ZERO,
            ),
            overtime_pay=sum(
                (
                    row.overtime_pay
                    for row in rows
                ),
                ZERO,
            ),
            additions=sum(
                (
                    row.additions_total
                    for row in rows
                ),
                ZERO,
            ),
            deductions=sum(
                (
                    row.deductions_total
                    for row in rows
                ),
                ZERO,
            ),
            gross_pay=sum(
                (
                    row.gross_pay
                    for row in rows
                ),
                ZERO,
            ),
            net_pay=sum(
                (
                    row.net_pay
                    for row in rows
                ),
                ZERO,
            ),
        )


__all__ = [
    "PayrollSummaryBuilder",
]