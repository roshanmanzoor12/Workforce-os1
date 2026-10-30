from __future__ import annotations

import uuid

from sqlalchemy import (
    select,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.modules.payroll.payslip_models import (
    PayrollPayslip,
)


class PayrollPayslipRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def get(
        self,
        *,
        payslip_id: uuid.UUID,
    ) -> PayrollPayslip | None:
        return await (
            self.session.scalar(
                select(
                    PayrollPayslip
                )
                .where(
                    PayrollPayslip.id
                    == payslip_id
                )
            )
        )

    async def get_for_run_employee(
        self,
        *,
        payroll_run_id: uuid.UUID,
        employee_id: uuid.UUID,
    ) -> PayrollPayslip | None:
        return await (
            self.session.scalar(
                select(
                    PayrollPayslip
                )
                .where(
                    PayrollPayslip
                    .payroll_run_id
                    == payroll_run_id,

                    PayrollPayslip
                    .employee_id
                    == employee_id,
                )
            )
        )

    async def list_for_employee(
        self,
        *,
        employee_id: uuid.UUID,
    ) -> list[
        PayrollPayslip
    ]:
        result = await (
            self.session.scalars(
                select(
                    PayrollPayslip
                )
                .where(
                    PayrollPayslip.employee_id
                    == employee_id
                )
                .order_by(
                    PayrollPayslip
                    .published_at
                    .desc(),
                )
            )
        )

        return list(
            result
        )

    async def list_for_run(
        self,
        *,
        payroll_run_id: uuid.UUID,
    ) -> list[
        PayrollPayslip
    ]:
        result = await (
            self.session.scalars(
                select(
                    PayrollPayslip
                )
                .where(
                    PayrollPayslip
                    .payroll_run_id
                    == payroll_run_id
                )
                .order_by(
                    PayrollPayslip
                    .employee_id
                    .asc(),
                )
            )
        )

        return list(
            result
        )

    async def create(
        self,
        payslip: PayrollPayslip,
    ) -> PayrollPayslip:
        self.session.add(
            payslip
        )

        await self.session.flush()

        await self.session.refresh(
            payslip
        )

        return payslip


__all__ = [
    "PayrollPayslipRepository",
]