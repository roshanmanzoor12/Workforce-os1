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
    field_validator,
    model_validator,
)

from app.modules.payroll.models import (
    CompensationBasis,
    PayrollAdjustmentType,
    PayrollCalculationStatus,
    PayrollRunStatus,
)


# =========================================================
# BASE
# =========================================================


class ORMModel(
    BaseModel
):
    model_config = ConfigDict(
        from_attributes=True
    )


# =========================================================
# COMPENSATION
# =========================================================


class CompensationContractCreateRequest(
    BaseModel
):
    employee_id: uuid.UUID

    basis: CompensationBasis

    base_amount: Decimal = Field(
        ge=Decimal(
            "0"
        )
    )

    currency: str = Field(
        min_length=3,
        max_length=3,
    )

    effective_from: date

    effective_to: (
        date | None
    ) = None

    standard_day_minutes: int = Field(
        default=480,
        gt=0,
        le=1440,
    )

    monthly_divisor_days: Decimal = Field(
        default=Decimal(
            "22"
        ),
        gt=Decimal(
            "0"
        ),
    )

    overtime_multiplier: Decimal = Field(
        default=Decimal(
            "1.5"
        ),
        ge=Decimal(
            "0"
        ),
    )

    overtime_enabled: bool = True

    notes: str | None = Field(
        default=None,
        max_length=5000,
    )

    @field_validator(
        "currency"
    )
    @classmethod
    def normalize_currency(
        cls,
        value: str,
    ) -> str:
        value = (
            value.strip()
            .upper()
        )

        if not value.isalpha():
            raise ValueError(
                "currency must contain "
                "exactly three letters."
            )

        return value

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


class CompensationContractUpdateRequest(
    BaseModel
):
    base_amount: (
        Decimal | None
    ) = Field(
        default=None,
        ge=Decimal(
            "0"
        ),
    )

    currency: (
        str | None
    ) = Field(
        default=None,
        min_length=3,
        max_length=3,
    )

    effective_to: (
        date | None
    ) = None

    standard_day_minutes: (
        int | None
    ) = Field(
        default=None,
        gt=0,
        le=1440,
    )

    monthly_divisor_days: (
        Decimal | None
    ) = Field(
        default=None,
        gt=Decimal(
            "0"
        ),
    )

    overtime_multiplier: (
        Decimal | None
    ) = Field(
        default=None,
        ge=Decimal(
            "0"
        ),
    )

    overtime_enabled: (
        bool | None
    ) = None

    notes: (
        str | None
    ) = Field(
        default=None,
        max_length=5000,
    )

    is_active: (
        bool | None
    ) = None

    @field_validator(
        "currency"
    )
    @classmethod
    def normalize_currency(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        value = (
            value.strip()
            .upper()
        )

        if not value.isalpha():
            raise ValueError(
                "currency must contain "
                "exactly three letters."
            )

        return value


class CompensationContractResponse(
    ORMModel
):
    id: uuid.UUID

    employee_id: uuid.UUID

    basis: CompensationBasis

    base_amount: Decimal

    currency: str

    effective_from: date

    effective_to: (
        date | None
    )

    standard_day_minutes: int

    monthly_divisor_days: Decimal

    overtime_multiplier: Decimal

    overtime_enabled: bool

    notes: (
        str | None
    )

    is_active: bool

    created_by_user_id: (
        uuid.UUID | None
    )

    created_at: datetime
    updated_at: datetime


# =========================================================
# PAYROLL RUN
# =========================================================


class PayrollRunCreateRequest(
    BaseModel
):
    period_start: date
    period_end: date

    cutoff_date: (
        date | None
    ) = None

    currency: str = Field(
        min_length=3,
        max_length=3,
    )

    notes: str | None = Field(
        default=None,
        max_length=5000,
    )

    @field_validator(
        "currency"
    )
    @classmethod
    def normalize_currency(
        cls,
        value: str,
    ) -> str:
        return (
            value.strip()
            .upper()
        )

    @model_validator(
        mode="after"
    )
    def validate_dates(
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
            self.cutoff_date
            is not None
            and self.cutoff_date
            > self.period_end
        ):
            raise ValueError(
                "cutoff_date cannot be "
                "after period_end."
            )

        return self


class PayrollRunResponse(
    ORMModel
):
    id: uuid.UUID

    period_start: date
    period_end: date

    cutoff_date: (
        date | None
    )

    currency: str

    status: PayrollRunStatus

    policy_version: str

    notes: (
        str | None
    )

    created_by_user_id: (
        uuid.UUID | None
    )

    approved_by_user_id: (
        uuid.UUID | None
    )

    approved_at: (
        datetime | None
    )

    locked_by_user_id: (
        uuid.UUID | None
    )

    locked_at: (
        datetime | None
    )

    paid_by_user_id: (
        uuid.UUID | None
    )

    paid_at: (
        datetime | None
    )

    created_at: datetime
    updated_at: datetime


# =========================================================
# CALCULATION INPUT
# =========================================================


class PayrollCalculationInput(
    BaseModel
):
    employee_id: uuid.UUID

    compensation_contract_id: (
        uuid.UUID
    )

    basis: CompensationBasis

    base_amount: Decimal = Field(
        ge=Decimal(
            "0"
        )
    )

    currency: str

    standard_day_minutes: int = Field(
        gt=0
    )

    monthly_divisor_days: Decimal = Field(
        gt=Decimal(
            "0"
        )
    )

    overtime_multiplier: Decimal = Field(
        ge=Decimal(
            "0"
        )
    )

    overtime_enabled: bool

    scheduled_minutes: int = Field(
        ge=0
    )

    actual_work_minutes: int = Field(
        ge=0
    )

    paid_leave_minutes: int = Field(
        default=0,
        ge=0,
    )

    unpaid_leave_minutes: int = Field(
        default=0,
        ge=0,
    )

    overtime_minutes: int = Field(
        default=0,
        ge=0,
    )

    additions_total: Decimal = Field(
        default=Decimal(
            "0"
        ),
        ge=Decimal(
            "0"
        ),
    )

    deductions_total: Decimal = Field(
        default=Decimal(
            "0"
        ),
        ge=Decimal(
            "0"
        ),
    )


class PayrollCalculationPreview(
    BaseModel
):
    employee_id: uuid.UUID

    currency: str

    daily_rate: Decimal
    hourly_rate: Decimal
    minute_rate: Decimal

    scheduled_minutes: int
    payable_minutes: int

    paid_leave_minutes: int
    unpaid_leave_minutes: int
    overtime_minutes: int

    base_pay: Decimal
    overtime_pay: Decimal

    additions_total: Decimal
    deductions_total: Decimal

    gross_pay: Decimal
    net_pay: Decimal


class PayrollCalculationResponse(
    ORMModel
):
    id: uuid.UUID

    payroll_run_id: uuid.UUID
    employee_id: uuid.UUID

    compensation_contract_id: (
        uuid.UUID
    )

    status: (
        PayrollCalculationStatus
    )

    currency: str

    base_amount: Decimal

    daily_rate: Decimal
    hourly_rate: Decimal
    minute_rate: Decimal

    scheduled_minutes: int
    payable_minutes: int

    paid_leave_minutes: int
    unpaid_leave_minutes: int
    overtime_minutes: int

    base_pay: Decimal
    overtime_pay: Decimal

    additions_total: Decimal
    deductions_total: Decimal

    gross_pay: Decimal
    net_pay: Decimal

    source_snapshot: dict
    explanation_snapshot: dict

    policy_version: str

    calculated_by_user_id: (
        uuid.UUID | None
    )

    calculated_at: datetime


# =========================================================
# ADJUSTMENT
# =========================================================


class PayrollAdjustmentCreateRequest(
    BaseModel
):
    employee_id: uuid.UUID

    adjustment_type: (
        PayrollAdjustmentType
    )

    amount: Decimal = Field(
        gt=Decimal(
            "0"
        )
    )

    reason: str = Field(
        min_length=1,
        max_length=500,
    )


class PayrollAdjustmentResponse(
    ORMModel
):
    id: uuid.UUID

    payroll_run_id: uuid.UUID
    employee_id: uuid.UUID

    adjustment_type: (
        PayrollAdjustmentType
    )

    amount: Decimal

    reason: str

    created_by_user_id: uuid.UUID

    created_at: datetime


__all__ = [
    "CompensationContractCreateRequest",
    "CompensationContractUpdateRequest",
    "CompensationContractResponse",
    "PayrollRunCreateRequest",
    "PayrollRunResponse",
    "PayrollCalculationInput",
    "PayrollCalculationPreview",
    "PayrollCalculationResponse",
    "PayrollAdjustmentCreateRequest",
    "PayrollAdjustmentResponse",
]