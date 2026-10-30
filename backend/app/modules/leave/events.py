from __future__ import annotations

import uuid
from dataclasses import (
    dataclass,
)
from datetime import (
    date,
    datetime,
)


LEAVE_REQUEST_CREATED_EVENT = (
    "leave.request.created"
)

LEAVE_REQUEST_APPROVED_EVENT = (
    "leave.request.approved"
)

LEAVE_REQUEST_REJECTED_EVENT = (
    "leave.request.rejected"
)

LEAVE_REQUEST_CANCELLED_EVENT = (
    "leave.request.cancelled"
)

LEAVE_POLICY_UPDATED_EVENT = (
    "leave.policy.updated"
)

LEAVE_BALANCE_ADJUSTED_EVENT = (
    "leave.balance.adjusted"
)


@dataclass(
    frozen=True,
    slots=True,
)
class LeaveDomainEvent:
    event_type: str

    workspace_id: uuid.UUID
    actor_user_id: uuid.UUID

    occurred_at: datetime


@dataclass(
    frozen=True,
    slots=True,
)
class LeaveRequestChangedEvent(
    LeaveDomainEvent
):
    request_id: uuid.UUID

    employee_id: uuid.UUID

    start_date: date
    end_date: date


@dataclass(
    frozen=True,
    slots=True,
)
class LeavePolicyChangedEvent(
    LeaveDomainEvent
):
    leave_type_id: uuid.UUID


@dataclass(
    frozen=True,
    slots=True,
)
class LeaveBalanceAdjustedEvent(
    LeaveDomainEvent
):
    employee_id: uuid.UUID

    leave_type_id: uuid.UUID

    balance_year: int


__all__ = [
    "LEAVE_REQUEST_CREATED_EVENT",
    "LEAVE_REQUEST_APPROVED_EVENT",
    "LEAVE_REQUEST_REJECTED_EVENT",
    "LEAVE_REQUEST_CANCELLED_EVENT",
    "LEAVE_POLICY_UPDATED_EVENT",
    "LEAVE_BALANCE_ADJUSTED_EVENT",
    "LeaveDomainEvent",
    "LeaveRequestChangedEvent",
    "LeavePolicyChangedEvent",
    "LeaveBalanceAdjustedEvent",
]