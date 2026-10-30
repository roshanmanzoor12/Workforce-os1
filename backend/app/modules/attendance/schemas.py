from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from app.modules.attendance.enums import (
    AttendanceEventType,
    AttendanceSource,
    AttendanceStatus,
)


class AttendanceSchemaBase(
    BaseModel
):
    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )


class AttendanceEventCreateRequest(
    AttendanceSchemaBase
):
    event_type: AttendanceEventType
    occurred_at: datetime

    source: AttendanceSource = (
        AttendanceSource.WEB
    )

    notes: str | None = Field(
        default=None,
        max_length=1000,
    )

    @field_validator(
        "notes",
        mode="before",
    )
    @classmethod
    def normalize_notes(
        cls,
        value,
    ):
        if value is None:
            return None

        if not isinstance(
            value,
            str,
        ):
            return value

        value = value.strip()

        return value or None


class AttendanceRecordUpdateRequest(
    AttendanceSchemaBase
):
    status: (
        AttendanceStatus | None
    ) = None

    source: (
        AttendanceSource | None
    ) = None

    notes: str | None = Field(
        default=None,
        max_length=2000,
    )

    @field_validator(
        "notes",
        mode="before",
    )
    @classmethod
    def normalize_notes(
        cls,
        value,
    ):
        if value is None:
            return None

        if not isinstance(
            value,
            str,
        ):
            return value

        value = value.strip()

        return value or None


class AttendanceEventPublic(
    AttendanceSchemaBase
):
    id: uuid.UUID

    attendance_record_id: uuid.UUID
    employee_id: uuid.UUID

    event_type: AttendanceEventType
    source: AttendanceSource

    occurred_at: datetime

    actor_user_id: uuid.UUID | None
    notes: str | None

    created_at: datetime
    updated_at: datetime


class AttendanceRecordPublic(
    AttendanceSchemaBase
):
    id: uuid.UUID

    employee_id: uuid.UUID
    attendance_date: date

    status: AttendanceStatus
    source: AttendanceSource

    check_in_at: datetime | None
    check_out_at: datetime | None

    worked_minutes: int
    break_minutes: int

    notes: str | None

    created_by_user_id: uuid.UUID | None
    updated_by_user_id: uuid.UUID | None

    created_at: datetime
    updated_at: datetime


class AttendanceRecordDetailResponse(
    AttendanceSchemaBase
):
    attendance: AttendanceRecordPublic

    events: list[
        AttendanceEventPublic
    ] = Field(
        default_factory=list
    )


class AttendanceRecordResponse(
    AttendanceSchemaBase
):
    message: str
    attendance: AttendanceRecordPublic


class AttendanceEventResponse(
    AttendanceSchemaBase
):
    message: str
    event: AttendanceEventPublic


class AttendanceListResponse(
    AttendanceSchemaBase
):
    attendance: list[
        AttendanceRecordPublic
    ] = Field(
        default_factory=list
    )

    total: int = Field(
        ge=0,
    )


class AttendanceSummaryResponse(
    AttendanceSchemaBase
):
    employee_id: uuid.UUID

    start_date: date
    end_date: date

    present_days: int = 0
    absent_days: int = 0
    late_days: int = 0
    half_days: int = 0
    leave_days: int = 0
    holiday_days: int = 0

    worked_minutes: int = 0
    break_minutes: int = 0


# Compatibility aliases.
AttendanceDayUpdateRequest = (
    AttendanceRecordUpdateRequest
)
AttendanceDayPublic = (
    AttendanceRecordPublic
)
AttendanceDayDetailResponse = (
    AttendanceRecordDetailResponse
)
AttendanceDayResponse = (
    AttendanceRecordResponse
)


__all__ = [
    "AttendanceEventCreateRequest",
    "AttendanceRecordUpdateRequest",
    "AttendanceDayUpdateRequest",
    "AttendanceEventPublic",
    "AttendanceRecordPublic",
    "AttendanceDayPublic",
    "AttendanceRecordDetailResponse",
    "AttendanceDayDetailResponse",
    "AttendanceRecordResponse",
    "AttendanceDayResponse",
    "AttendanceEventResponse",
    "AttendanceListResponse",
    "AttendanceSummaryResponse",
]