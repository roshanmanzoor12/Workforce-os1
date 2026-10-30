from __future__ import annotations

import uuid
from decimal import Decimal

from pydantic import (
    BaseModel,
    Field,
)

from app.modules.payroll.models import (
    PayrollRunStatus,
)


class PayrollRunSummaryResponse(
    BaseModel
):
    run_id: uuid.UUID

    status: PayrollRunStatus

    currency: str

    employees: int = Field(
        ge=0
    )

    scheduled_minutes: int = Field(
        ge=0
    )

    payable_minutes: int = Field(
        ge=0
    )

    paid_leave_minutes: int = Field(
        ge=0
    )

    unpaid_leave_minutes: int = Field(
        ge=0
    )

    overtime_minutes: int = Field(
        ge=0
    )

    base_pay: Decimal

    overtime_pay: Decimal

    additions: Decimal

    deductions: Decimal

    gross_pay: Decimal

    net_pay: Decimal


__all__ = [
    "PayrollRunSummaryResponse",
]