from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


class PerformanceSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


class ReviewCycleCreate(PerformanceSchema):
    name: str = Field(
        min_length=1,
        max_length=200,
    )

    starts_on: date

    ends_on: date

    @field_validator("name")
    @classmethod
    def validate_name(
        cls,
        value: str,
    ) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "name must not be empty"
            )

        return value

    @field_validator("ends_on")
    @classmethod
    def validate_date_range(
        cls,
        value: date,
        info,
    ) -> date:
        starts_on = info.data.get(
            "starts_on"
        )

        if (
            starts_on is not None
            and value < starts_on
        ):
            raise ValueError(
                "ends_on must be on or after starts_on"
            )

        return value


class ReviewCreate(PerformanceSchema):
    cycle_id: UUID

    employee_id: UUID

    rating: int = Field(
        ge=1,
        le=5,
    )

    summary: str = Field(
        min_length=1,
        max_length=5000,
    )

    @field_validator("summary")
    @classmethod
    def validate_summary(
        cls,
        value: str,
    ) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "summary must not be empty"
            )

        return value


class ReviewCycleUpdate(PerformanceSchema):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )

    starts_on: date | None = None

    ends_on: date | None = None

    status: str | None = Field(
        default=None,
        max_length=50,
    )

    @field_validator("name")
    @classmethod
    def validate_optional_name(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError(
                "name must not be empty"
            )

        return value


class ReviewUpdate(PerformanceSchema):
    rating: int | None = Field(
        default=None,
        ge=1,
        le=5,
    )

    summary: str | None = Field(
        default=None,
        min_length=1,
        max_length=5000,
    )

    status: str | None = Field(
        default=None,
        max_length=50,
    )

    @field_validator("summary")
    @classmethod
    def validate_optional_summary(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError(
                "summary must not be empty"
            )

        return value


class CyclePublic(PerformanceSchema):
    id: UUID

    workspace_id: UUID

    name: str

    starts_on: date

    ends_on: date

    status: str

    created_at: datetime | None = None

    updated_at: datetime | None = None


class ReviewPublic(PerformanceSchema):
    id: UUID

    workspace_id: UUID

    cycle_id: UUID

    employee_id: UUID

    rating: int

    summary: str

    status: str

    created_at: datetime | None = None

    updated_at: datetime | None = None


class CycleList(PerformanceSchema):
    items: list[CyclePublic]

    total: int


class ReviewList(PerformanceSchema):
    items: list[ReviewPublic]

    total: int


__all__ = [
    "ReviewCycleCreate",
    "ReviewCreate",
    "ReviewCycleUpdate",
    "ReviewUpdate",
    "CyclePublic",
    "ReviewPublic",
    "CycleList",
    "ReviewList",
]