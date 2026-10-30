from __future__ import annotations

import uuid
from dataclasses import (
    dataclass,
)
from datetime import (
    date,
    datetime,
)
from decimal import Decimal


COMPENSATION_CONTRACT_CREATED_EVENT = (
    "payroll.compensation_contract.created"
)

COMPENSATION_CONTRACT_UPDATED_EVENT = (
    "payroll.compensation_contract.updated"
)

PAYROLL_RUN_CREATED_EVENT = (
    "payroll.run.created"
)

PAYROLL_RUN_CALCULATED_EVENT = (
    "payroll.run.calculated"
)

PAYROLL_ADJUSTMENT_CREATED_EVENT = (
    "payroll.adjustment.created"
)

PAYROLL_RUN_APPROVED_EVENT = (
    "payroll.run.approved"
)

PAYROLL_RUN_LOCKED_EVENT = (
    "payroll.run.locked"
)

PAYROLL_RUN_PAID_EVENT = (
    "payroll.run.paid"
)


@dataclass(
    frozen=True,
    slots=True,
)
class CompensationContractEvent:
    event_type: str

    workspace_id: uuid.UUID
    actor_user_id: uuid.UUID

    contract_id: uuid.UUID
    employee_id: uuid.UUID

    occurred_at: datetime


@dataclass(
    frozen=True,
    slots=True,
)
class PayrollRunEvent:
    event_type: str

    workspace_id: uuid.UUID
    actor_user_id: uuid.UUID

    run_id: uuid.UUID

    period_start: date
    period_end: date

    occurred_at: datetime


@dataclass(
    frozen=True,
    slots=True,
)
class PayrollCalculationEvent:
    event_type: str

    workspace_id: uuid.UUID
    actor_user_id: uuid.UUID

    run_id: uuid.UUID
    employee_id: uuid.UUID

    net_pay: Decimal
    currency: str

    occurred_at: datetime


@dataclass(
    frozen=True,
    slots=True,
)
class PayrollAdjustmentEvent:
    event_type: str

    workspace_id: uuid.UUID
    actor_user_id: uuid.UUID

    run_id: uuid.UUID
    employee_id: uuid.UUID
    adjustment_id: uuid.UUID

    amount: Decimal

    occurred_at: datetime


__all__ = [
    "COMPENSATION_CONTRACT_CREATED_EVENT",
    "COMPENSATION_CONTRACT_UPDATED_EVENT",
    "PAYROLL_RUN_CREATED_EVENT",
    "PAYROLL_RUN_CALCULATED_EVENT",
    "PAYROLL_ADJUSTMENT_CREATED_EVENT",
    "PAYROLL_RUN_APPROVED_EVENT",
    "PAYROLL_RUN_LOCKED_EVENT",
    "PAYROLL_RUN_PAID_EVENT",
    "CompensationContractEvent",
    "PayrollRunEvent",
    "PayrollCalculationEvent",
    "PayrollAdjustmentEvent",
]