from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class AppObservationRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    process_name: str = Field(
        min_length=1,
        max_length=255,
    )

    executable_path: str | None = Field(
        default=None,
        max_length=4096,
    )

    window_title: str | None = Field(
        default=None,
        max_length=4096,
    )

    observed_at: datetime

    @field_validator(
        "process_name"
    )
    @classmethod
    def normalize_process_name(
        cls,
        value: str,
    ) -> str:
        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "process_name cannot be blank."
            )

        return normalized

    @field_validator(
        "executable_path",
        "window_title",
    )
    @classmethod
    def normalize_optional_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = value.strip()

        return normalized or None

    @model_validator(
        mode="after"
    )
    def validate_timezone(
        self,
    ) -> "AppObservationRequest":
        if self.observed_at.tzinfo is None:
            raise ValueError(
                "observed_at must be timezone-aware."
            )

        return self


class AppObservationResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    event_id: UUID
    device_uuid: UUID
    employee_id: UUID | None

    app_key: str
    process_name: str
    executable_path: str | None
    window_title: str | None

    observed_at: datetime
    received_at: datetime


class AppUsageIntervalResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID
    device_id: UUID
    employee_id: UUID | None

    app_key: str
    process_name: str
    executable_path: str | None
    last_window_title: str | None

    status: str

    started_at: datetime
    ended_at: datetime | None
    last_observed_at: datetime

    duration_seconds: int = Field(
        ge=0,
    )


class AppTrackingProcessingResult(BaseModel):
    interval_id: UUID

    created: bool
    closed_previous_interval: bool
    ignored_observation: bool

    app_key: str
    process_name: str
    status: str

    duration_seconds: int = Field(
        ge=0,
    )


class AppUsageSummaryItem(BaseModel):
    app_key: str
    process_name: str

    duration_seconds: int = Field(
        ge=0,
    )


class AppUsageSummaryResponse(BaseModel):
    items: list[AppUsageSummaryItem]

    total_seconds: int = Field(
        ge=0,
    )


__all__ = [
    "AppObservationRequest",
    "AppObservationResponse",
    "AppUsageIntervalResponse",
    "AppTrackingProcessingResult",
    "AppUsageSummaryItem",
    "AppUsageSummaryResponse",
]