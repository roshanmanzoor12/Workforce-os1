from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


__all__ = [
    "ActivityStateRequest",
    "ActivityStateResponse",
    "ActivityStatusResponse",
]


class ActivityStateRequest(BaseModel):
    """
    Active/idle observation sent by an authenticated WorkforceOS Agent.

    Device identity, workspace identity, tenant database, and employee
    assignment are resolved server-side from authenticated device context.

    No keystrokes, typed text, clipboard contents, or input payloads
    are accepted.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    state: str = Field(
        min_length=4,
        max_length=20,
        description="Current endpoint state: active or idle.",
    )

    idle_seconds: int = Field(
        ge=0,
        le=86_400,
        description="Seconds since the most recent user input.",
    )

    last_input_at: datetime | None = Field(
        default=None,
        description="Agent-observed UTC timestamp of the most recent input.",
    )

    observed_at: datetime = Field(
        description="Agent-observed UTC timestamp for this state sample.",
    )

    @model_validator(
        mode="after"
    )
    def validate_state_consistency(
        self,
    ) -> "ActivityStateRequest":
        normalized_state = (
            self.state
            .strip()
            .lower()
        )

        if normalized_state not in {
            "active",
            "idle",
        }:
            raise ValueError(
                "state must be either 'active' or 'idle'"
            )

        self.state = normalized_state

        if (
            self.state == "active"
            and self.idle_seconds < 0
        ):
            raise ValueError(
                "active state cannot have negative idle_seconds"
            )

        if (
            self.last_input_at is not None
            and self.last_input_at > self.observed_at
        ):
            raise ValueError(
                "last_input_at cannot be later than observed_at"
            )

        return self


class ActivityStateResponse(BaseModel):
    """
    Server acknowledgement for a successfully recorded activity state.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    event_id: UUID

    device_uuid: UUID

    employee_id: UUID | None

    state: str

    idle_seconds: int

    last_input_at: datetime | None

    observed_at: datetime

    received_at: datetime


class ActivityStatusResponse(BaseModel):
    """
    Workspace/dashboard-facing current activity state for a device.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    device_uuid: UUID

    employee_id: UUID | None

    state: str

    idle_seconds: int

    last_input_at: datetime | None

    observed_at: datetime | None

    received_at: datetime | None