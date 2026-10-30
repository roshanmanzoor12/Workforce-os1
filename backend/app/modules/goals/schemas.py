from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

from app.modules.goals.enums import (
    GoalPriority,
    GoalStatus,
)


class GoalSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True,
    )


class GoalCreateRequest(GoalSchema):
    owner_employee_id: uuid.UUID

    title: str = Field(
        min_length=1,
        max_length=200,
    )

    description: str | None = Field(
        default=None,
        max_length=10000,
    )

    priority: GoalPriority = (
        GoalPriority.MEDIUM
    )

    start_date: date | None = None
    due_date: date | None = None

    @model_validator(mode="after")
    def validate_dates(
        self,
    ) -> "GoalCreateRequest":
        if (
            self.start_date is not None
            and self.due_date is not None
            and self.due_date < self.start_date
        ):
            raise ValueError(
                "due_date cannot be before "
                "start_date"
            )

        return self


class GoalUpdateRequest(GoalSchema):
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )

    description: str | None = Field(
        default=None,
        max_length=10000,
    )

    priority: GoalPriority | None = None
    status: GoalStatus | None = None

    progress_percent: int | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    start_date: date | None = None
    due_date: date | None = None


class GoalPublic(GoalSchema):
    id: uuid.UUID
    owner_employee_id: uuid.UUID

    title: str
    description: str | None

    status: GoalStatus
    priority: GoalPriority

    progress_percent: int

    start_date: date | None
    due_date: date | None
    completed_at: datetime | None

    created_at: datetime
    updated_at: datetime


class GoalListResponse(GoalSchema):
    items: list[GoalPublic]
    total: int = Field(
        ge=0,
    )


__all__ = [
    "GoalCreateRequest",
    "GoalUpdateRequest",
    "GoalPublic",
    "GoalListResponse",
]