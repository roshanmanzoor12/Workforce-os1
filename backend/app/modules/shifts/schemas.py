from __future__ import annotations

import uuid
from datetime import (
    date,
    datetime,
    time,
)

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

from app.modules.holidays.models import (
    HolidayTreatment,
)
from app.modules.shifts.models import (
    ScheduleExceptionType,
    SchedulePublicationStatus,
    ShiftAssignmentTargetType,
)


class ORMModel(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )


# =========================================================
# WORKING DAYS
# =========================================================


class ShiftWorkingDayInput(BaseModel):
    weekday: int = Field(
        ge=0,
        le=6,
    )

    is_working_day: bool = True


class ShiftWorkingDayResponse(ORMModel):
    id: uuid.UUID
    shift_id: uuid.UUID
    weekday: int
    is_working_day: bool


# =========================================================
# SHIFT TEMPLATE
# =========================================================


class ShiftCreateRequest(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=120,
    )

    timezone: str = Field(
        min_length=1,
        max_length=64,
    )

    start_time: time
    end_time: time

    break_minutes: int = Field(
        default=0,
        ge=0,
        le=1440,
    )

    standard_paid_minutes: (
        int | None
    ) = Field(
        default=None,
        ge=0,
        le=1440,
    )

    grace_before_minutes: int = Field(
        default=0,
        ge=0,
        le=240,
    )

    grace_after_minutes: int = Field(
        default=0,
        ge=0,
        le=240,
    )

    overtime_after_minutes: (
        int | None
    ) = Field(
        default=None,
        ge=0,
        le=1440,
    )

    is_overnight: bool = False

    working_days: list[
        ShiftWorkingDayInput
    ] = Field(
        default_factory=list,
    )

    @model_validator(
        mode="after"
    )
    def validate_shift(
        self,
    ):
        if (
            not self.is_overnight
            and self.end_time
            <= self.start_time
        ):
            raise ValueError(
                "end_time must be after "
                "start_time unless "
                "is_overnight=true."
            )

        weekdays = [
            item.weekday
            for item
            in self.working_days
        ]

        if (
            len(weekdays)
            != len(
                set(weekdays)
            )
        ):
            raise ValueError(
                "working_days cannot contain "
                "duplicate weekdays."
            )

        return self


class ShiftUpdateRequest(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=120,
    )

    timezone: str | None = Field(
        default=None,
        min_length=1,
        max_length=64,
    )

    start_time: time | None = None
    end_time: time | None = None

    break_minutes: int | None = Field(
        default=None,
        ge=0,
        le=1440,
    )

    standard_paid_minutes: (
        int | None
    ) = Field(
        default=None,
        ge=0,
        le=1440,
    )

    grace_before_minutes: (
        int | None
    ) = Field(
        default=None,
        ge=0,
        le=240,
    )

    grace_after_minutes: (
        int | None
    ) = Field(
        default=None,
        ge=0,
        le=240,
    )

    overtime_after_minutes: (
        int | None
    ) = Field(
        default=None,
        ge=0,
        le=1440,
    )

    is_overnight: bool | None = None
    is_active: bool | None = None

    working_days: (
        list[ShiftWorkingDayInput]
        | None
    ) = None


class ShiftResponse(ORMModel):
    id: uuid.UUID

    name: str
    timezone: str

    start_time: time
    end_time: time

    break_minutes: int
    standard_paid_minutes: int | None

    grace_before_minutes: int
    grace_after_minutes: int

    overtime_after_minutes: int | None

    is_overnight: bool
    is_active: bool

    created_at: datetime
    updated_at: datetime


class ShiftDetailResponse(
    ShiftResponse
):
    working_days: list[
        ShiftWorkingDayResponse
    ] = Field(
        default_factory=list,
    )


# =========================================================
# ASSIGNMENTS
# =========================================================


class ShiftAssignmentCreateRequest(
    BaseModel
):
    shift_id: uuid.UUID

    target_type: (
        ShiftAssignmentTargetType
    )

    target_id: uuid.UUID

    effective_from: date
    effective_to: date | None = None

    priority: int = Field(
        default=0,
        ge=-1000,
        le=1000,
    )

    @model_validator(
        mode="after"
    )
    def validate_dates(
        self,
    ):
        if (
            self.effective_to
            is not None
            and self.effective_to
            < self.effective_from
        ):
            raise ValueError(
                "effective_to cannot be "
                "before effective_from."
            )

        return self


class ShiftAssignmentUpdateRequest(
    BaseModel
):
    shift_id: uuid.UUID | None = None

    effective_from: date | None = None
    effective_to: date | None = None

    priority: int | None = Field(
        default=None,
        ge=-1000,
        le=1000,
    )


class ShiftAssignmentResponse(
    ORMModel
):
    id: uuid.UUID

    shift_id: uuid.UUID

    target_type: (
        ShiftAssignmentTargetType
    )

    target_id: uuid.UUID

    effective_from: date
    effective_to: date | None

    priority: int

    created_at: datetime
    updated_at: datetime


# =========================================================
# SCHEDULE EXCEPTION
# =========================================================


class ScheduleExceptionCreateRequest(
    BaseModel
):
    employee_id: uuid.UUID

    exception_date: date

    exception_type: (
        ScheduleExceptionType
    )

    custom_start_time: time | None = None
    custom_end_time: time | None = None

    break_minutes: (
        int | None
    ) = Field(
        default=None,
        ge=0,
        le=1440,
    )

    reason: str | None = Field(
        default=None,
        max_length=500,
    )

    @model_validator(
        mode="after"
    )
    def validate_exception(
        self,
    ):
        if (
            self.exception_type
            == (
                ScheduleExceptionType
                .CUSTOM_SHIFT
            )
            and (
                self.custom_start_time
                is None
                or self.custom_end_time
                is None
            )
        ):
            raise ValueError(
                "Custom shift exception "
                "requires custom_start_time "
                "and custom_end_time."
            )

        return self


class ScheduleExceptionUpdateRequest(
    BaseModel
):
    exception_type: (
        ScheduleExceptionType
        | None
    ) = None

    custom_start_time: time | None = None
    custom_end_time: time | None = None

    break_minutes: (
        int | None
    ) = Field(
        default=None,
        ge=0,
        le=1440,
    )

    reason: str | None = Field(
        default=None,
        max_length=500,
    )


class ScheduleExceptionResponse(
    ORMModel
):
    id: uuid.UUID
    employee_id: uuid.UUID

    exception_date: date

    exception_type: (
        ScheduleExceptionType
    )

    custom_start_time: time | None
    custom_end_time: time | None

    break_minutes: int | None

    reason: str | None

    created_by_user_id: (
        uuid.UUID | None
    )

    created_at: datetime
    updated_at: datetime


# =========================================================
# PUBLICATION
# =========================================================


class SchedulePublishRequest(
    BaseModel
):
    period_start: date
    period_end: date

    note: str | None = Field(
        default=None,
        max_length=500,
    )

    @model_validator(
        mode="after"
    )
    def validate_range(
        self,
    ):
        if (
            self.period_end
            < self.period_start
        ):
            raise ValueError(
                "period_end cannot be "
                "before period_start."
            )

        if (
            self.period_end
            - self.period_start
        ).days > 366:
            raise ValueError(
                "Schedule publication "
                "cannot exceed 366 days."
            )

        return self


class SchedulePublicationResponse(
    ORMModel
):
    id: uuid.UUID

    period_start: date
    period_end: date

    status: (
        SchedulePublicationStatus
    )

    published_by_user_id: (
        uuid.UUID | None
    )

    published_at: datetime | None

    note: str | None

    created_at: datetime


# =========================================================
# RESOLVED SCHEDULE
# =========================================================


class ResolvedScheduleDayResponse(
    BaseModel
):
    employee_id: uuid.UUID
    schedule_date: date

    source: str

    shift_id: uuid.UUID | None = None

    timezone: str | None = None

    start_time: time | None = None
    end_time: time | None = None

    break_minutes: int = 0

    scheduled_minutes: int = 0

    payable_minutes: int = 0

    is_working_day: bool = False

    is_published: bool = False

    exception_id: uuid.UUID | None = None

    # -----------------------------------------------------
    # HOLIDAY CONTEXT
    # -----------------------------------------------------

    is_holiday: bool = False

    holiday_id: uuid.UUID | None = None

    holiday_name: str | None = None

    holiday_treatment: (
        HolidayTreatment | None
    ) = None


__all__ = [
    "ShiftWorkingDayInput",
    "ShiftWorkingDayResponse",
    "ShiftCreateRequest",
    "ShiftUpdateRequest",
    "ShiftResponse",
    "ShiftDetailResponse",
    "ShiftAssignmentCreateRequest",
    "ShiftAssignmentUpdateRequest",
    "ShiftAssignmentResponse",
    "ScheduleExceptionCreateRequest",
    "ScheduleExceptionUpdateRequest",
    "ScheduleExceptionResponse",
    "SchedulePublishRequest",
    "SchedulePublicationResponse",
    "ResolvedScheduleDayResponse",
]