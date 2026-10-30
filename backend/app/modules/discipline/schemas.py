from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class DisciplineSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )


class IncidentCreate(
    DisciplineSchema,
):
    employee_id: uuid.UUID

    category: str = Field(
        min_length=1,
        max_length=80,
    )

    summary: str = Field(
        min_length=1,
        max_length=500,
    )

    details: str | None = Field(
        default=None,
        max_length=10000,
    )

    action: str | None = Field(
        default=None,
        max_length=120,
    )


class IncidentUpdate(
    DisciplineSchema,
):
    status: str | None = Field(
        default=None,
        pattern=(
            "^(open|under_review|"
            "resolved|dismissed)$"
        ),
    )

    action: str | None = Field(
        default=None,
        max_length=120,
    )


class IncidentPublic(
    DisciplineSchema,
):
    id: uuid.UUID
    employee_id: uuid.UUID
    reported_by_user_id: uuid.UUID
    category: str
    summary: str
    details: str | None
    action: str | None
    status: str
    created_at: datetime
    resolved_at: datetime | None


class IncidentList(
    DisciplineSchema,
):
    items: list[IncidentPublic]
    total: int = Field(
        ge=0,
    )


__all__ = [
    "IncidentCreate",
    "IncidentUpdate",
    "IncidentPublic",
    "IncidentList",
]