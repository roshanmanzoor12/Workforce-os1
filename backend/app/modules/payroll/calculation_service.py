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
from app.modules.payroll.schemas import (
    PayrollCalculationInput,
)
from app.modules.payroll.service import (
    PayrollService,
)
from app.modules.payroll.source_assembler import (
    PayrollSourceAssembler,
)
from app.modules.payroll.source_schemas import (
    PayrollCalculateRequest,
    PayrollRunCalculationResponse,
)


class PayrollCalculationService:
    """
    Authoritative Payroll calculation orchestration.

    Request accepts employee identities only.

    Salary, schedule, attendance, Leave, holiday and adjustment
    amounts are loaded by the backend.
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

        self.payroll = (
            PayrollService(
                session
            )
        )

        self.sources = (
            PayrollSourceAssembler(
                session
            )
        )

        self.employees = (
            EmployeeRepository(
                session
            )
        )

    async def _targets(
        self,
        request: PayrollCalculateRequest,
    ):
        if request.employee_ids:
            result = []

            seen: set[
                uuid.UUID
            ] = set()

            for employee_id in (
                request.employee_ids
            ):
                if employee_id in seen:
                    continue

                seen.add(
                    employee_id
                )

                employee = await (
                    self.employees
                    .get_employee_by_id(
                        employee_id
                    )
                )

                if (
                    employee is None
                    or not employee.is_active
                ):
                    raise HTTPException(
                        status_code=(
                            status
                            .HTTP_404_NOT_FOUND
                        ),
                        detail=(
                            "Active payroll "
                            "employee not found."
                        ),
                    )

                result.append(
                    employee
                )

            return result

        return list(
            await self.employees
            .list_employees()
        )

    async def calculate_run(
        self,
        *,
        run_id: uuid.UUID,
        request: PayrollCalculateRequest,
        actor_user_id: uuid.UUID,
    ) -> PayrollRunCalculationResponse:
        run = await (
            self.payroll.require_run(
                run_id
            )
        )

        if run.status not in {
            PayrollRunStatus.DRAFT,
            PayrollRunStatus.REVIEW,
        }:
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Payroll run is not "
                    "recalculable."
                ),
            )

        employees = await (
            self._targets(
                request
            )
        )

        processed: list[
            uuid.UUID
        ] = []

        skipped: list[
            uuid.UUID
        ] = []

        for employee in employees:
            try:
                (
                    contract,
                    source,
                ) = await (
                    self.sources.assemble(
                        run_id=run.id,
                        employee_id=(
                            employee.id
                        ),
                        period_start=(
                            run.period_start
                        ),
                        period_end=(
                            run.period_end
                        ),
                    )
                )

            except HTTPException as exc:
                # No compensation contract = not a payroll subject.
                if (
                    exc.status_code
                    == status.HTTP_409_CONFLICT
                    and "no active compensation"
                    in str(
                        exc.detail
                    ).lower()
                ):
                    skipped.append(
                        employee.id
                    )

                    continue

                raise

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
                        "Compensation contract "
                        "currency does not match "
                        "payroll run currency."
                    ),
                )

            calculation_input = (
                PayrollCalculationInput(
                    employee_id=(
                        employee.id
                    ),
                    compensation_contract_id=(
                        contract.id
                    ),
                    basis=(
                        contract.basis
                    ),
                    base_amount=(
                        contract.base_amount
                    ),
                    currency=(
                        contract.currency
                    ),
                    standard_day_minutes=(
                        contract
                        .standard_day_minutes
                    ),
                    monthly_divisor_days=(
                        contract
                        .monthly_divisor_days
                    ),
                    overtime_multiplier=(
                        contract
                        .overtime_multiplier
                    ),
                    overtime_enabled=(
                        contract
                        .overtime_enabled
                    ),
                    scheduled_minutes=(
                        source.schedule
                        .payable_minutes
                    ),
                    actual_work_minutes=(
                        source.attendance
                        .actual_work_minutes
                    ),
                    paid_leave_minutes=(
                        source.leave
                        .paid_leave_minutes
                    ),
                    unpaid_leave_minutes=(
                        source.leave
                        .unpaid_leave_minutes
                    ),
                    overtime_minutes=(
                        source.attendance
                        .overtime_minutes
                    ),
                    additions_total=(
                        source.adjustments
                        .additions_total
                    ),
                    deductions_total=(
                        source.adjustments
                        .deductions_total
                    ),
                )
            )

            await (
                self.payroll
                .persist_calculation(
                    run_id=run.id,
                    request=(
                        calculation_input
                    ),
                    actor_user_id=(
                        actor_user_id
                    ),
                    source_snapshot=(
                        source
                        .source_snapshot()
                    ),
                )
            )

            processed.append(
                employee.id
            )

        return PayrollRunCalculationResponse(
            run_id=run.id,
            processed_employees=len(
                processed
            ),
            skipped_employees=len(
                skipped
            ),
            processed_employee_ids=(
                processed
            ),
            skipped_employee_ids=(
                skipped
            ),
        )


__all__ = [
    "PayrollCalculationService",
]