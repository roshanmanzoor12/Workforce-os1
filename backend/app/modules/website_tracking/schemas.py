from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


class WebsiteObservationRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    browser_name: str = Field(
        min_length=1,
        max_length=100,
    )

    browser_process_name: str = Field(
        min_length=1,
        max_length=255,
    )

    domain: str = Field(
        min_length=1,
        max_length=2048,
    )

    page_url: str | None = Field(
        default=None,
        max_length=8192,
    )

    page_title: str | None = Field(
        default=None,
        max_length=1024,
    )

    observed_at: datetime

    @field_validator(
        "browser_name",
        "browser_process_name",
        "domain",
        mode="before",
    )
    @classmethod
    def strip_required_strings(
        cls,
        value: object,
    ) -> object:
        if isinstance(value, str):
            return value.strip()

        return value

    @field_validator(
        "page_url",
        "page_title",
        mode="before",
    )
    @classmethod
    def normalize_optional_strings(
        cls,
        value: object,
    ) -> object:
        if value is None:
            return None

        if isinstance(value, str):
            value = value.strip()

            if not value:
                return None

        return value

    @field_validator(
        "observed_at",
    )
    @classmethod
    def require_timezone(
        cls,
        value: datetime,
    ) -> datetime:
        if value.tzinfo is None:
            raise ValueError(
                "observed_at must be timezone-aware."
            )

        return value


class WebsiteObservationResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: uuid.UUID
    device_id: uuid.UUID
    employee_id: uuid.UUID | None

    browser_name: str
    browser_process_name: str

    domain: str
    normalized_domain: str

    page_url: str | None
    page_title: str | None

    observed_at: datetime
    received_at: datetime
    created_at: datetime


class WebsiteUsageIntervalResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: uuid.UUID
    device_id: uuid.UUID
    employee_id: uuid.UUID | None

    browser_name: str
    browser_process_name: str

    domain: str
    normalized_domain: str

    status: str

    started_at: datetime
    ended_at: datetime | None
    last_observed_at: datetime

    duration_seconds: int

    last_page_url: str | None
    last_page_title: str | None


class WebsiteObservationProcessingResult(BaseModel):
    observation: WebsiteObservationResponse

    current_interval: (
        WebsiteUsageIntervalResponse
        | None
    )

    previous_interval_closed: bool = False
    ignored_as_old: bool = False


__all__ = [
    "WebsiteObservationRequest",
    "WebsiteObservationResponse",
    "WebsiteUsageIntervalResponse",
    "WebsiteObservationProcessingResult",
]