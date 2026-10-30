from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)


class WorkSessionResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID

    device_id: UUID
    employee_id: UUID | None

    status: str
    current_state: str

    started_at: datetime
    ended_at: datetime | None
    last_observed_at: datetime

    active_seconds: int = Field(
        ge=0,
    )

    idle_seconds: int = Field(
        ge=0,
    )

    total_seconds: int = Field(
        ge=0,
    )


class WorkSessionListResponse(BaseModel):
    items: list[WorkSessionResponse]

    total: int = Field(
        ge=0,
    )


class WorkSessionSummaryResponse(BaseModel):
    session_count: int = Field(
        ge=0,
    )

    active_seconds: int = Field(
        ge=0,
    )

    idle_seconds: int = Field(
        ge=0,
    )

    total_seconds: int = Field(
        ge=0,
    )

    first_started_at: datetime | None
    last_observed_at: datetime | None


class WorkSessionCloseRequest(BaseModel):
    ended_at: datetime

    @model_validator(
        mode="after"
    )
    def validate_request(
        self,
    ) -> "WorkSessionCloseRequest":
        if self.ended_at.tzinfo is None:
            raise ValueError(
                "ended_at must be timezone-aware."
            )

        return self


class WorkSessionProcessingResult(BaseModel):
    session_id: UUID

    created: bool
    closed_previous_session: bool
    ignored_event: bool

    status: str
    current_state: str

    active_seconds: int = Field(
        ge=0,
    )

    idle_seconds: int = Field(
        ge=0,
    )

    total_seconds: int = Field(
        ge=0,
    )


__all__ = [
    "WorkSessionResponse",
    "WorkSessionListResponse",
    "WorkSessionSummaryResponse",
    "WorkSessionCloseRequest",
    "WorkSessionProcessingResult",
]