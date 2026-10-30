from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from pydantic import (
    BaseModel,
    Field,
)


class PayrollCalculateRequest(
    BaseModel
):
    """
    Browser may choose which employees to calculate,
    but it never supplies authoritative salary/time math.
    """

    employee_ids: (
        list[uuid.UUID] | None
    ) = None


class PayrollScheduleDaySource(
    BaseModel
):
    schedule_date: date

    shift_id: (
        uuid.UUID | None
    ) = None

    source: str

    scheduled_minutes: int = Field(
        ge=0
    )

    payable_minutes: int = Field(
        ge=0
    )

    is_working_day: bool

    is_published: bool


class PayrollScheduleSource(
    BaseModel
):
    employee_id: uuid.UUID

    period_start: date
    period_end: date

    scheduled_minutes: int = Field(
        ge=0
    )

    payable_minutes: int = Field(
        ge=0
    )

    days: list[
        PayrollScheduleDaySource
    ] = Field(
        default_factory=list
    )


class PayrollAttendanceSource(
    BaseModel
):
    employee_id: uuid.UUID

    actual_work_minutes: int = Field(
        ge=0
    )

    overtime_minutes: int = Field(
        ge=0
    )

    attendance_source_ids: list[
        str
    ] = Field(
        default_factory=list
    )


class PayrollLeaveSource(
    BaseModel
):
    employee_id: uuid.UUID

    paid_leave_minutes: int = Field(
        ge=0
    )

    unpaid_leave_minutes: int = Field(
        ge=0
    )

    leave_request_ids: list[
        uuid.UUID
    ] = Field(
        default_factory=list
    )


class PayrollAdjustmentSource(
    BaseModel
):
    employee_id: uuid.UUID

    additions_total: Decimal = Field(
        ge=Decimal(
            "0"
        )
    )

    deductions_total: Decimal = Field(
        ge=Decimal(
            "0"
        )
    )

    adjustment_ids: list[
        uuid.UUID
    ] = Field(
        default_factory=list
    )


class PayrollEmployeeSourceBundle(
    BaseModel
):
    employee_id: uuid.UUID

    compensation_contract_id: (
        uuid.UUID
    )

    schedule: PayrollScheduleSource

    attendance: PayrollAttendanceSource

    leave: PayrollLeaveSource

    adjustments: (
        PayrollAdjustmentSource
    )

    def source_snapshot(
        self,
    ) -> dict:
        return {
            "employee_id": str(
                self.employee_id
            ),
            "compensation_contract_id": str(
                self.compensation_contract_id
            ),
            "schedule": (
                self.schedule.model_dump(
                    mode="json"
                )
            ),
            "attendance": (
                self.attendance.model_dump(
                    mode="json"
                )
            ),
            "leave": (
                self.leave.model_dump(
                    mode="json"
                )
            ),
            "adjustments": (
                self.adjustments.model_dump(
                    mode="json"
                )
            ),
        }


class PayrollRunCalculationResponse(
    BaseModel
):
    run_id: uuid.UUID

    processed_employees: int = Field(
        ge=0
    )

    skipped_employees: int = Field(
        ge=0
    )

    processed_employee_ids: list[
        uuid.UUID
    ] = Field(
        default_factory=list
    )

    skipped_employee_ids: list[
        uuid.UUID
    ] = Field(
        default_factory=list
    )


__all__ = [
    "PayrollCalculateRequest",
    "PayrollScheduleDaySource",
    "PayrollScheduleSource",
    "PayrollAttendanceSource",
    "PayrollLeaveSource",
    "PayrollAdjustmentSource",
    "PayrollEmployeeSourceBundle",
    "PayrollRunCalculationResponse",
]