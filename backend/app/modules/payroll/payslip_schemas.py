from __future__ import annotations

import uuid
from datetime import (
    date,
    datetime,
)
from decimal import Decimal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class PayslipORMModel(
    BaseModel
):
    model_config = ConfigDict(
        from_attributes=True
    )


class PayrollPayslipSummaryResponse(
    PayslipORMModel
):
    id: uuid.UUID

    payroll_run_id: uuid.UUID

    employee_id: uuid.UUID

    currency: str

    gross_pay: Decimal

    deductions_total: Decimal

    net_pay: Decimal

    published_at: datetime


class PayrollPayslipDetailResponse(
    PayrollPayslipSummaryResponse
):
    payroll_calculation_id: (
        uuid.UUID
    )

    additions_total: Decimal

    policy_version: str

    statement_snapshot: dict

    published_by_user_id: (
        uuid.UUID
    )

    created_at: datetime


class PayrollPayslipPeriod(
    BaseModel
):
    period_start: date

    period_end: date


class PayrollPayslipPublishResponse(
    BaseModel
):
    payroll_run_id: uuid.UUID

    published_count: int = Field(
        ge=0
    )

    existing_count: int = Field(
        ge=0
    )

    payslip_ids: list[
        uuid.UUID
    ] = Field(
        default_factory=list
    )


__all__ = [
    "PayrollPayslipSummaryResponse",
    "PayrollPayslipDetailResponse",
    "PayrollPayslipPeriod",
    "PayrollPayslipPublishResponse",
]