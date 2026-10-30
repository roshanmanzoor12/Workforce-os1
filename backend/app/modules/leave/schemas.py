from __future__ import annotations

import uuid
from datetime import (
    date,
    datetime,
)
from decimal import Decimal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

from app.modules.leave.models import (
    LeaveRequestStatus,
)


class LeaveSchema(
    BaseModel
):
    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
    )


class LeaveTypeCreateRequest(
    LeaveSchema
):
    name: str = Field(
        min_length=1,
        max_length=120,
    )

    code: str = Field(
        min_length=1,
        max_length=50,
    )

    description: (
        str | None
    ) = None

    is_paid: bool = True

    requires_approval: bool = True


class LeaveTypeUpdateRequest(
    LeaveSchema
):
    name: (
        str | None
    ) = Field(
        default=None,
        min_length=1,
        max_length=120,
    )

    description: (
        str | None
    ) = None

    is_paid: (
        bool | None
    ) = None

    requires_approval: (
        bool | None
    ) = None

    is_active: (
        bool | None
    ) = None


class LeaveTypeResponse(
    LeaveSchema
):
    id: uuid.UUID

    name: str
    code: str

    description: (
        str | None
    )

    is_paid: bool
    requires_approval: bool
    is_active: bool

    created_at: datetime
    updated_at: datetime


class LeavePolicyUpsertRequest(
    LeaveSchema
):
    annual_allowance_days: Decimal = (
        Field(
            default=Decimal("0"),
            ge=Decimal("0"),
        )
    )

    carry_forward_days: Decimal = (
        Field(
            default=Decimal("0"),
            ge=Decimal("0"),
        )
    )

    minimum_notice_days: int = Field(
        default=0,
        ge=0,
        le=365,
    )

    allow_negative_balance: bool = False

    is_active: bool = True


class LeavePolicyResponse(
    LeaveSchema
):
    id: uuid.UUID

    leave_type_id: uuid.UUID

    annual_allowance_days: Decimal
    carry_forward_days: Decimal

    minimum_notice_days: int

    allow_negative_balance: bool
    is_active: bool

    created_at: datetime
    updated_at: datetime


class LeaveBalanceResponse(
    LeaveSchema
):
    id: uuid.UUID

    employee_id: uuid.UUID
    leave_type_id: uuid.UUID

    balance_year: int

    allocated_days: Decimal
    carried_forward_days: Decimal
    adjustment_days: Decimal
    used_days: Decimal
    pending_days: Decimal

    available_days: Decimal

    updated_by_user_id: (
        uuid.UUID | None
    )

    created_at: datetime
    updated_at: datetime


class LeaveBalanceAdjustmentRequest(
    LeaveSchema
):
    adjustment_days: Decimal

    reason: str = Field(
        min_length=1,
        max_length=500,
    )


class LeaveRequestCreateRequest(
    LeaveSchema
):
    leave_type_id: uuid.UUID

    start_date: date
    end_date: date

    reason: (
        str | None
    ) = Field(
        default=None,
        max_length=2000,
    )

    @model_validator(
        mode="after"
    )
    def validate_dates(
        self,
    ):
        if (
            self.end_date
            < self.start_date
        ):
            raise ValueError(
                "end_date cannot be "
                "before start_date."
            )

        return self


class LeaveDecisionRequest(
    LeaveSchema
):
    note: (
        str | None
    ) = Field(
        default=None,
        max_length=2000,
    )


class LeaveRequestResponse(
    LeaveSchema
):
    id: uuid.UUID

    employee_id: uuid.UUID
    leave_type_id: uuid.UUID

    start_date: date
    end_date: date

    requested_days: Decimal

    status: LeaveRequestStatus

    reason: str | None
    decision_note: str | None

    created_by_user_id: (
        uuid.UUID | None
    )

    reviewed_by_user_id: (
        uuid.UUID | None
    )

    reviewed_at: (
        datetime | None
    )

    created_at: datetime
    updated_at: datetime


class LeaveRequestListResponse(
    LeaveSchema
):
    items: list[
        LeaveRequestResponse
    ] = Field(
        default_factory=list
    )

    total: int


__all__ = [
    "LeaveTypeCreateRequest",
    "LeaveTypeUpdateRequest",
    "LeaveTypeResponse",
    "LeavePolicyUpsertRequest",
    "LeavePolicyResponse",
    "LeaveBalanceResponse",
    "LeaveBalanceAdjustmentRequest",
    "LeaveRequestCreateRequest",
    "LeaveDecisionRequest",
    "LeaveRequestResponse",
    "LeaveRequestListResponse",
]