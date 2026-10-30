from __future__ import annotations

import uuid
from dataclasses import (
    dataclass,
)
from datetime import (
    date,
    datetime,
)


# =========================================================
# EVENT NAMES
# =========================================================


SHIFT_CREATED_EVENT = (
    "shift.created"
)

SHIFT_UPDATED_EVENT = (
    "shift.updated"
)

SHIFT_DEACTIVATED_EVENT = (
    "shift.deactivated"
)

SHIFT_ASSIGNMENT_CREATED_EVENT = (
    "shift.assignment.created"
)

SHIFT_ASSIGNMENT_UPDATED_EVENT = (
    "shift.assignment.updated"
)

SHIFT_ASSIGNMENT_DELETED_EVENT = (
    "shift.assignment.deleted"
)

SCHEDULE_EXCEPTION_CREATED_EVENT = (
    "schedule.exception.created"
)

SCHEDULE_EXCEPTION_UPDATED_EVENT = (
    "schedule.exception.updated"
)

SCHEDULE_EXCEPTION_DELETED_EVENT = (
    "schedule.exception.deleted"
)

SCHEDULE_PUBLISHED_EVENT = (
    "schedule.published"
)


# =========================================================
# BASE EVENT
# =========================================================


@dataclass(
    frozen=True,
    slots=True,
)
class ShiftDomainEvent:
    event_type: str

    workspace_id: uuid.UUID
    actor_user_id: uuid.UUID

    occurred_at: datetime


# =========================================================
# SHIFT EVENT
# =========================================================


@dataclass(
    frozen=True,
    slots=True,
)
class ShiftChangedEvent(
    ShiftDomainEvent
):
    shift_id: uuid.UUID


# =========================================================
# ASSIGNMENT EVENT
# =========================================================


@dataclass(
    frozen=True,
    slots=True,
)
class ShiftAssignmentChangedEvent(
    ShiftDomainEvent
):
    assignment_id: uuid.UUID

    shift_id: uuid.UUID

    target_type: str
    target_id: uuid.UUID


# =========================================================
# EXCEPTION EVENT
# =========================================================


@dataclass(
    frozen=True,
    slots=True,
)
class ScheduleExceptionChangedEvent(
    ShiftDomainEvent
):
    exception_id: uuid.UUID

    employee_id: uuid.UUID
    exception_date: date


# =========================================================
# PUBLICATION EVENT
# =========================================================


@dataclass(
    frozen=True,
    slots=True,
)
class SchedulePublishedEvent(
    ShiftDomainEvent
):
    publication_id: uuid.UUID

    period_start: date
    period_end: date


__all__ = [
    "SHIFT_CREATED_EVENT",
    "SHIFT_UPDATED_EVENT",
    "SHIFT_DEACTIVATED_EVENT",
    "SHIFT_ASSIGNMENT_CREATED_EVENT",
    "SHIFT_ASSIGNMENT_UPDATED_EVENT",
    "SHIFT_ASSIGNMENT_DELETED_EVENT",
    "SCHEDULE_EXCEPTION_CREATED_EVENT",
    "SCHEDULE_EXCEPTION_UPDATED_EVENT",
    "SCHEDULE_EXCEPTION_DELETED_EVENT",
    "SCHEDULE_PUBLISHED_EVENT",
    "ShiftDomainEvent",
    "ShiftChangedEvent",
    "ShiftAssignmentChangedEvent",
    "ScheduleExceptionChangedEvent",
    "SchedulePublishedEvent",
]