from __future__ import annotations

import uuid
from dataclasses import (
    dataclass,
)
from datetime import (
    date,
    datetime,
)


HOLIDAY_CREATED_EVENT = (
    "holiday.created"
)

HOLIDAY_UPDATED_EVENT = (
    "holiday.updated"
)

HOLIDAY_DEACTIVATED_EVENT = (
    "holiday.deactivated"
)


@dataclass(
    frozen=True,
    slots=True,
)
class HolidayDomainEvent:
    event_type: str

    workspace_id: uuid.UUID
    actor_user_id: uuid.UUID

    holiday_id: uuid.UUID

    holiday_date: date

    occurred_at: datetime


__all__ = [
    "HOLIDAY_CREATED_EVENT",
    "HOLIDAY_UPDATED_EVENT",
    "HOLIDAY_DEACTIVATED_EVENT",
    "HolidayDomainEvent",
]