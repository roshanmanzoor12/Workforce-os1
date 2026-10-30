from __future__ import annotations

import enum
import uuid
from datetime import (
    date,
    datetime,
    timezone,
)
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import (
    JSONB,
    UUID,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.db.tenant_base import (
    TenantBase,
)


# =========================================================
# TIME
# =========================================================


def utc_now() -> datetime:
    return datetime.now(
        timezone.utc
    )


# =========================================================
# ENUMS
# =========================================================


class CompensationBasis(
    str,
    enum.Enum,
):
    MONTHLY = "monthly"
    DAILY = "daily"
    HOURLY = "hourly"
    FIXED_CONTRACT = (
        "fixed_contract"
    )


class PayrollRunStatus(
    str,
    enum.Enum,
):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    LOCKED = "locked"
    PAID = "paid"
    VOID = "void"


class PayrollAdjustmentType(
    str,
    enum.Enum,
):
    ADDITION = "addition"
    DEDUCTION = "deduction"


class PayrollCalculationStatus(
    str,
    enum.Enum,
):
    CALCULATED = "calculated"
    EXCLUDED = "excluded"


# =========================================================
# COMPENSATION CONTRACT
# =========================================================


class CompensationContract(
    TenantBase
):
    """
    Employee compensation contract.

    Salary belongs to Employee compensation, never to workspace
    role. Multiple historical contracts may exist, but effective
    date ranges must be managed by the service layer.
    """

    __tablename__ = (
        "compensation_contracts"
    )

    __table_args__ = (
        Index(
            "ix_comp_contract_employee_dates",
            "employee_id",
            "effective_from",
            "effective_to",
        ),
        Index(
            "ix_comp_contract_active",
            "employee_id",
            "is_active",
        ),
        CheckConstraint(
            "base_amount >= 0",
            name=(
                "ck_compensation_"
                "base_amount_nonnegative"
            ),
        ),
        CheckConstraint(
            (
                "standard_day_minutes "
                "> 0"
            ),
            name=(
                "ck_compensation_"
                "standard_day_minutes_"
                "positive"
            ),
        ),
        CheckConstraint(
            (
                "monthly_divisor_days "
                "> 0"
            ),
            name=(
                "ck_compensation_"
                "monthly_divisor_positive"
            ),
        ),
    )

    id: Mapped[
        uuid.UUID
    ] = mapped_column(
        UUID(
            as_uuid=True
        ),
        primary_key=True,
        default=uuid.uuid4,
    )

    employee_id: Mapped[
        uuid.UUID
    ] = mapped_column(
        UUID(
            as_uuid=True
        ),
        ForeignKey(
            "employees.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    basis: Mapped[
        CompensationBasis
    ] = mapped_column(
        Enum(
            CompensationBasis,
            name=(
                "compensation_basis"
            ),
        ),
        nullable=False,
    )

    base_amount: Mapped[
        Decimal
    ] = mapped_column(
        Numeric(
            18,
            4,
        ),
        nullable=False,
    )

    currency: Mapped[
        str
    ] = mapped_column(
        String(
            3
        ),
        nullable=False,
    )

    effective_from: Mapped[
        date
    ] = mapped_column(
        Date(),
        nullable=False,
    )

    effective_to: Mapped[
        date | None
    ] = mapped_column(
        Date(),
        nullable=True,
    )

    standard_day_minutes: Mapped[
        int
    ] = mapped_column(
        Integer(),
        nullable=False,
        default=480,
    )

    monthly_divisor_days: Mapped[
        Decimal
    ] = mapped_column(
        Numeric(
            10,
            4,
        ),
        nullable=False,
        default=Decimal(
            "22"
        ),
    )

    overtime_multiplier: Mapped[
        Decimal
    ] = mapped_column(
        Numeric(
            8,
            4,
        ),
        nullable=False,
        default=Decimal(
            "1.5"
        ),
    )

    overtime_enabled: Mapped[
        bool
    ] = mapped_column(
        Boolean(),
        nullable=False,
        default=True,
    )

    notes: Mapped[
        str | None
    ] = mapped_column(
        Text(),
        nullable=True,
    )

    is_active: Mapped[
        bool
    ] = mapped_column(
        Boolean(),
        nullable=False,
        default=True,
    )

    created_by_user_id: Mapped[
        uuid.UUID | None
    ] = mapped_column(
        UUID(
            as_uuid=True
        ),
        nullable=True,
    )

    created_at: Mapped[
        datetime
    ] = mapped_column(
        DateTime(
            timezone=True
        ),
        nullable=False,
        default=utc_now,
    )

    updated_at: Mapped[
        datetime
    ] = mapped_column(
        DateTime(
            timezone=True
        ),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


# =========================================================
# PAYROLL RUN
# =========================================================


class PayrollRun(
    TenantBase
):
    __tablename__ = (
        "payroll_runs"
    )

    __table_args__ = (
        UniqueConstraint(
            "period_start",
            "period_end",
            "currency",
            name=(
                "uq_payroll_run_"
                "period_currency"
            ),
        ),
        Index(
            "ix_payroll_run_period",
            "period_start",
            "period_end",
        ),
        Index(
            "ix_payroll_run_status",
            "status",
        ),
        CheckConstraint(
            (
                "period_end >= "
                "period_start"
            ),
            name=(
                "ck_payroll_run_"
                "period_order"
            ),
        ),
    )

    id: Mapped[
        uuid.UUID
    ] = mapped_column(
        UUID(
            as_uuid=True
        ),
        primary_key=True,
        default=uuid.uuid4,
    )

    period_start: Mapped[
        date
    ] = mapped_column(
        Date(),
        nullable=False,
    )

    period_end: Mapped[
        date
    ] = mapped_column(
        Date(),
        nullable=False,
    )

    cutoff_date: Mapped[
        date | None
    ] = mapped_column(
        Date(),
        nullable=True,
    )

    currency: Mapped[
        str
    ] = mapped_column(
        String(
            3
        ),
        nullable=False,
    )

    status: Mapped[
        PayrollRunStatus
    ] = mapped_column(
        Enum(
            PayrollRunStatus,
            name=(
                "payroll_run_status"
            ),
        ),
        nullable=False,
        default=(
            PayrollRunStatus.DRAFT
        ),
    )

    policy_version: Mapped[
        str
    ] = mapped_column(
        String(
            100
        ),
        nullable=False,
        default="phase12.3-v1",
    )

    notes: Mapped[
        str | None
    ] = mapped_column(
        Text(),
        nullable=True,
    )

    created_by_user_id: Mapped[
        uuid.UUID | None
    ] = mapped_column(
        UUID(
            as_uuid=True
        ),
        nullable=True,
    )

    approved_by_user_id: Mapped[
        uuid.UUID | None
    ] = mapped_column(
        UUID(
            as_uuid=True
        ),
        nullable=True,
    )

    approved_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(
            timezone=True
        ),
        nullable=True,
    )

    locked_by_user_id: Mapped[
        uuid.UUID | None
    ] = mapped_column(
        UUID(
            as_uuid=True
        ),
        nullable=True,
    )

    locked_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(
            timezone=True
        ),
        nullable=True,
    )

    paid_by_user_id: Mapped[
        uuid.UUID | None
    ] = mapped_column(
        UUID(
            as_uuid=True
        ),
        nullable=True,
    )

    paid_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(
            timezone=True
        ),
        nullable=True,
    )

    created_at: Mapped[
        datetime
    ] = mapped_column(
        DateTime(
            timezone=True
        ),
        nullable=False,
        default=utc_now,
    )

    updated_at: Mapped[
        datetime
    ] = mapped_column(
        DateTime(
            timezone=True
        ),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    calculations: Mapped[
        list[
            "PayrollCalculation"
        ]
    ] = relationship(
        back_populates="run",
        cascade=(
            "all, "
            "delete-orphan"
        ),
        passive_deletes=True,
    )

    adjustments: Mapped[
        list[
            "PayrollAdjustment"
        ]
    ] = relationship(
        back_populates="run",
        cascade=(
            "all, "
            "delete-orphan"
        ),
        passive_deletes=True,
    )


# =========================================================
# CALCULATION SNAPSHOT
# =========================================================


class PayrollCalculation(
    TenantBase
):
    """
    Authoritative immutable calculation snapshot for one employee
    within one payroll run.

    Later recalculation should create/replace draft snapshots before
    approval. Once the run is locked, the service must reject silent
    mutation.
    """

    __tablename__ = (
        "payroll_calculations"
    )

    __table_args__ = (
        UniqueConstraint(
            "payroll_run_id",
            "employee_id",
            name=(
                "uq_payroll_calculation_"
                "run_employee"
            ),
        ),
        Index(
            "ix_payroll_calc_employee",
            "employee_id",
        ),
        CheckConstraint(
            "scheduled_minutes >= 0",
            name=(
                "ck_payroll_calc_"
                "scheduled_minutes"
            ),
        ),
        CheckConstraint(
            "payable_minutes >= 0",
            name=(
                "ck_payroll_calc_"
                "payable_minutes"
            ),
        ),
        CheckConstraint(
            "overtime_minutes >= 0",
            name=(
                "ck_payroll_calc_"
                "overtime_minutes"
            ),
        ),
        CheckConstraint(
            (
                "unpaid_leave_minutes "
                ">= 0"
            ),
            name=(
                "ck_payroll_calc_"
                "unpaid_leave_minutes"
            ),
        ),
    )

    id: Mapped[
        uuid.UUID
    ] = mapped_column(
        UUID(
            as_uuid=True
        ),
        primary_key=True,
        default=uuid.uuid4,
    )

    payroll_run_id: Mapped[
        uuid.UUID
    ] = mapped_column(
        UUID(
            as_uuid=True
        ),
        ForeignKey(
            "payroll_runs.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    employee_id: Mapped[
        uuid.UUID
    ] = mapped_column(
        UUID(
            as_uuid=True
        ),
        ForeignKey(
            "employees.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    compensation_contract_id: Mapped[
        uuid.UUID
    ] = mapped_column(
        UUID(
            as_uuid=True
        ),
        ForeignKey(
            (
                "compensation_contracts"
                ".id"
            ),
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    status: Mapped[
        PayrollCalculationStatus
    ] = mapped_column(
        Enum(
            PayrollCalculationStatus,
            name=(
                "payroll_calculation_"
                "status"
            ),
        ),
        nullable=False,
        default=(
            PayrollCalculationStatus
            .CALCULATED
        ),
    )

    currency: Mapped[
        str
    ] = mapped_column(
        String(
            3
        ),
        nullable=False,
    )

    base_amount: Mapped[
        Decimal
    ] = mapped_column(
        Numeric(
            18,
            4,
        ),
        nullable=False,
    )

    daily_rate: Mapped[
        Decimal
    ] = mapped_column(
        Numeric(
            18,
            6,
        ),
        nullable=False,
    )

    hourly_rate: Mapped[
        Decimal
    ] = mapped_column(
        Numeric(
            18,
            6,
        ),
        nullable=False,
    )

    minute_rate: Mapped[
        Decimal
    ] = mapped_column(
        Numeric(
            18,
            8,
        ),
        nullable=False,
    )

    scheduled_minutes: Mapped[
        int
    ] = mapped_column(
        Integer(),
        nullable=False,
        default=0,
    )

    payable_minutes: Mapped[
        int
    ] = mapped_column(
        Integer(),
        nullable=False,
        default=0,
    )

    paid_leave_minutes: Mapped[
        int
    ] = mapped_column(
        Integer(),
        nullable=False,
        default=0,
    )

    unpaid_leave_minutes: Mapped[
        int
    ] = mapped_column(
        Integer(),
        nullable=False,
        default=0,
    )

    overtime_minutes: Mapped[
        int
    ] = mapped_column(
        Integer(),
        nullable=False,
        default=0,
    )

    base_pay: Mapped[
        Decimal
    ] = mapped_column(
        Numeric(
            18,
            4,
        ),
        nullable=False,
        default=Decimal(
            "0"
        ),
    )

    overtime_pay: Mapped[
        Decimal
    ] = mapped_column(
        Numeric(
            18,
            4,
        ),
        nullable=False,
        default=Decimal(
            "0"
        ),
    )

    additions_total: Mapped[
        Decimal
    ] = mapped_column(
        Numeric(
            18,
            4,
        ),
        nullable=False,
        default=Decimal(
            "0"
        ),
    )

    deductions_total: Mapped[
        Decimal
    ] = mapped_column(
        Numeric(
            18,
            4,
        ),
        nullable=False,
        default=Decimal(
            "0"
        ),
    )

    gross_pay: Mapped[
        Decimal
    ] = mapped_column(
        Numeric(
            18,
            4,
        ),
        nullable=False,
        default=Decimal(
            "0"
        ),
    )

    net_pay: Mapped[
        Decimal
    ] = mapped_column(
        Numeric(
            18,
            4,
        ),
        nullable=False,
        default=Decimal(
            "0"
        ),
    )

    source_snapshot: Mapped[
        dict
    ] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    explanation_snapshot: Mapped[
        dict
    ] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    policy_version: Mapped[
        str
    ] = mapped_column(
        String(
            100
        ),
        nullable=False,
    )

    calculated_by_user_id: Mapped[
        uuid.UUID | None
    ] = mapped_column(
        UUID(
            as_uuid=True
        ),
        nullable=True,
    )

    calculated_at: Mapped[
        datetime
    ] = mapped_column(
        DateTime(
            timezone=True
        ),
        nullable=False,
        default=utc_now,
    )

    run: Mapped[
        PayrollRun
    ] = relationship(
        back_populates=(
            "calculations"
        ),
    )


# =========================================================
# ADJUSTMENT
# =========================================================


class PayrollAdjustment(
    TenantBase
):
    __tablename__ = (
        "payroll_adjustments"
    )

    __table_args__ = (
        Index(
            "ix_payroll_adjustment_run",
            "payroll_run_id",
        ),
        Index(
            (
                "ix_payroll_adjustment_"
                "employee"
            ),
            "employee_id",
        ),
        CheckConstraint(
            "amount > 0",
            name=(
                "ck_payroll_adjustment_"
                "amount_positive"
            ),
        ),
    )

    id: Mapped[
        uuid.UUID
    ] = mapped_column(
        UUID(
            as_uuid=True
        ),
        primary_key=True,
        default=uuid.uuid4,
    )

    payroll_run_id: Mapped[
        uuid.UUID
    ] = mapped_column(
        UUID(
            as_uuid=True
        ),
        ForeignKey(
            "payroll_runs.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    employee_id: Mapped[
        uuid.UUID
    ] = mapped_column(
        UUID(
            as_uuid=True
        ),
        ForeignKey(
            "employees.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    adjustment_type: Mapped[
        PayrollAdjustmentType
    ] = mapped_column(
        Enum(
            PayrollAdjustmentType,
            name=(
                "payroll_adjustment_"
                "type"
            ),
        ),
        nullable=False,
    )

    amount: Mapped[
        Decimal
    ] = mapped_column(
        Numeric(
            18,
            4,
        ),
        nullable=False,
    )

    reason: Mapped[
        str
    ] = mapped_column(
        String(
            500
        ),
        nullable=False,
    )

    created_by_user_id: Mapped[
        uuid.UUID
    ] = mapped_column(
        UUID(
            as_uuid=True
        ),
        nullable=False,
    )

    created_at: Mapped[
        datetime
    ] = mapped_column(
        DateTime(
            timezone=True
        ),
        nullable=False,
        default=utc_now,
    )

    run: Mapped[
        PayrollRun
    ] = relationship(
        back_populates=(
            "adjustments"
        ),
    )


__all__ = [
    "CompensationBasis",
    "PayrollRunStatus",
    "PayrollAdjustmentType",
    "PayrollCalculationStatus",
    "CompensationContract",
    "PayrollRun",
    "PayrollCalculation",
    "PayrollAdjustment",
]