from __future__ import annotations

import uuid
from datetime import date
from enum import StrEnum

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


class LifecycleSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )


class OnboardingStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class OffboardingStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class OnboardingCreateRequest(LifecycleSchema):
    employee_id: uuid.UUID
    start_date: date | None = None
    tasks: list[str] = Field(default_factory=list)
    notes: str | None = None

    @field_validator("tasks")
    @classmethod
    def normalize_tasks(cls, value: list[str]) -> list[str]:
        return [
            item.strip()
            for item in value
            if item.strip()
        ]

    @field_validator("notes")
    @classmethod
    def normalize_notes(cls, value):
        if isinstance(value, str):
            return value.strip() or None
        return value


class OnboardingUpdateRequest(LifecycleSchema):
    status: OnboardingStatus | None = None
    start_date: date | None = None
    completed_date: date | None = None
    tasks: list[str] | None = None
    notes: str | None = None

    @field_validator("tasks")
    @classmethod
    def normalize_tasks(cls, value):
        if value is None:
            return None

        return [
            item.strip()
            for item in value
            if item.strip()
        ]


class OnboardingResponse(LifecycleSchema):
    id: uuid.UUID
    employee_id: uuid.UUID
    status: OnboardingStatus
    start_date: date | None
    completed_date: date | None
    tasks: list[str]
    notes: str | None


class OffboardingCreateRequest(LifecycleSchema):
    employee_id: uuid.UUID
    last_working_date: date
    reason: str = Field(
        min_length=2,
        max_length=200,
    )
    tasks: list[str] = Field(default_factory=list)
    notes: str | None = None

    @field_validator("reason")
    @classmethod
    def normalize_reason(cls, value: str) -> str:
        return value.strip()

    @field_validator("tasks")
    @classmethod
    def normalize_tasks(cls, value: list[str]) -> list[str]:
        return [
            item.strip()
            for item in value
            if item.strip()
        ]


class OffboardingUpdateRequest(LifecycleSchema):
    status: OffboardingStatus | None = None
    last_working_date: date | None = None
    reason: str | None = Field(
        default=None,
        min_length=2,
        max_length=200,
    )
    tasks: list[str] | None = None
    notes: str | None = None

    @field_validator("reason")
    @classmethod
    def normalize_reason(cls, value):
        if isinstance(value, str):
            return value.strip() or None
        return value


class OffboardingResponse(LifecycleSchema):
    id: uuid.UUID
    employee_id: uuid.UUID
    status: OffboardingStatus
    last_working_date: date
    reason: str
    tasks: list[str]
    notes: str | None


__all__ = [
    "OnboardingStatus",
    "OffboardingStatus",
    "OnboardingCreateRequest",
    "OnboardingUpdateRequest",
    "OnboardingResponse",
    "OffboardingCreateRequest",
    "OffboardingUpdateRequest",
    "OffboardingResponse",
]