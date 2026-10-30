from __future__ import annotations

import uuid

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
from app.modules.payroll.models import (
    PayrollRunStatus,
)
from app.modules.payroll.payslip_models import (
    PayrollPayslip,
)
from app.modules.payroll.payslip_repository import (
    PayrollPayslipRepository,
)
from app.modules.payroll.payslip_schemas import (
    PayrollPayslipPublishResponse,
)
from app.modules.payroll.repository import (
    PayrollRepository,
)


class PayrollPayslipService:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

        self.payroll = (
            PayrollRepository(
                session
            )
        )

        self.payslips = (
            PayrollPayslipRepository(
                session
            )
        )

        self.employees = (
            EmployeeRepository(
                session
            )
        )

    async def require_payslip(
        self,
        payslip_id: uuid.UUID,
    ) -> PayrollPayslip:
        payslip = await (
            self.payslips.get(
                payslip_id=(
                    payslip_id
                )
            )
        )

        if payslip is None:
            raise HTTPException(
                status_code=(
                    status
                    .HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Payslip not found."
                ),
            )

        return payslip

    async def list_employee_payslips(
        self,
        *,
        employee_id: uuid.UUID,
    ):
        return await (
            self.payslips
            .list_for_employee(
                employee_id=(
                    employee_id
                )
            )
        )

    async def publish_run(
        self,
        *,
        run_id: uuid.UUID,
        actor_user_id: uuid.UUID,
    ) -> PayrollPayslipPublishResponse:
        run = await (
            self.payroll.get_run(
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

        if (
            run.status
            != PayrollRunStatus.PAID
        ):
            raise HTTPException(
                status_code=(
                    status
                    .HTTP_409_CONFLICT
                ),
                detail=(
                    "Payslips can only be "
                    "published for a paid "
                    "Payroll run."
                ),
            )

        calculations = await (
            self.payroll
            .list_calculations(
                run_id=run.id
            )
        )

        published_ids: list[
            uuid.UUID
        ] = []

        published_count = 0
        existing_count = 0

        for calculation in calculations:
            existing = await (
                self.payslips
                .get_for_run_employee(
                    payroll_run_id=(
                        run.id
                    ),
                    employee_id=(
                        calculation
                        .employee_id
                    ),
                )
            )

            if existing is not None:
                existing_count += 1

                published_ids.append(
                    existing.id
                )

                continue

            snapshot = {
                "payroll_run": {
                    "id": str(
                        run.id
                    ),
                    "period_start": (
                        run.period_start
                        .isoformat()
                    ),
                    "period_end": (
                        run.period_end
                        .isoformat()
                    ),
                    "currency": (
                        run.currency
                    ),
                    "status": (
                        run.status.value
                    ),
                    "policy_version": (
                        run.policy_version
                    ),
                },
                "calculation": {
                    "id": str(
                        calculation.id
                    ),
                    "employee_id": str(
                        calculation
                        .employee_id
                    ),
                    "compensation_contract_id": str(
                        calculation
                        .compensation_contract_id
                    ),
                    "scheduled_minutes": (
                        calculation
                        .scheduled_minutes
                    ),
                    "payable_minutes": (
                        calculation
                        .payable_minutes
                    ),
                    "paid_leave_minutes": (
                        calculation
                        .paid_leave_minutes
                    ),
                    "unpaid_leave_minutes": (
                        calculation
                        .unpaid_leave_minutes
                    ),
                    "overtime_minutes": (
                        calculation
                        .overtime_minutes
                    ),
                    "base_pay": str(
                        calculation.base_pay
                    ),
                    "overtime_pay": str(
                        calculation
                        .overtime_pay
                    ),
                    "additions_total": str(
                        calculation
                        .additions_total
                    ),
                    "deductions_total": str(
                        calculation
                        .deductions_total
                    ),
                    "gross_pay": str(
                        calculation.gross_pay
                    ),
                    "net_pay": str(
                        calculation.net_pay
                    ),
                    "source_snapshot": (
                        calculation
                        .source_snapshot
                    ),
                    "explanation_snapshot": (
                        calculation
                        .explanation_snapshot
                    ),
                    "policy_version": (
                        calculation
                        .policy_version
                    ),
                },
            }

            payslip = PayrollPayslip(
                payroll_run_id=(
                    run.id
                ),
                payroll_calculation_id=(
                    calculation.id
                ),
                employee_id=(
                    calculation.employee_id
                ),
                currency=(
                    calculation.currency
                ),
                gross_pay=(
                    calculation.gross_pay
                ),
                additions_total=(
                    calculation
                    .additions_total
                ),
                deductions_total=(
                    calculation
                    .deductions_total
                ),
                net_pay=(
                    calculation.net_pay
                ),
                policy_version=(
                    calculation
                    .policy_version
                ),
                statement_snapshot=(
                    snapshot
                ),
                published_by_user_id=(
                    actor_user_id
                ),
            )

            payslip = await (
                self.payslips.create(
                    payslip
                )
            )

            published_count += 1

            published_ids.append(
                payslip.id
            )

        await self.session.commit()

        return (
            PayrollPayslipPublishResponse(
                payroll_run_id=run.id,
                published_count=(
                    published_count
                ),
                existing_count=(
                    existing_count
                ),
                payslip_ids=(
                    published_ids
                ),
            )
        )


__all__ = [
    "PayrollPayslipService",
]