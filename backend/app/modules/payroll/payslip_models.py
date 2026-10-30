from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import (
    JSONB,
    UUID,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.db.tenant_base import (
    TenantBase,
)


def utc_now() -> datetime:
    return datetime.utcnow()


class PayrollPayslip(
    TenantBase
):
    """
    Immutable employee-facing payroll statement.

    A payslip stores the finalized calculation snapshot rather than
    recalculating from mutable Attendance/Leave/Schedule data later.
    """

    __tablename__ = (
        "payroll_payslips"
    )

    __table_args__ = (
        UniqueConstraint(
            "payroll_run_id",
            "employee_id",
            name=(
                "uq_payroll_payslip_"
                "run_employee"
            ),
        ),
        Index(
            "ix_payroll_payslips_employee",
            "employee_id",
            "published_at",
        ),
        Index(
            "ix_payroll_payslips_run",
            "payroll_run_id",
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
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    payroll_calculation_id: Mapped[
        uuid.UUID
    ] = mapped_column(
        UUID(
            as_uuid=True
        ),
        ForeignKey(
            "payroll_calculations.id",
            ondelete="RESTRICT",
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

    currency: Mapped[
        str
    ] = mapped_column(
        String(
            3
        ),
        nullable=False,
    )

    gross_pay: Mapped[
        Decimal
    ] = mapped_column(
        Numeric(
            18,
            4,
        ),
        nullable=False,
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

    net_pay: Mapped[
        Decimal
    ] = mapped_column(
        Numeric(
            18,
            4,
        ),
        nullable=False,
    )

    policy_version: Mapped[
        str
    ] = mapped_column(
        String(
            100
        ),
        nullable=False,
    )

    statement_snapshot: Mapped[
        dict
    ] = mapped_column(
        JSONB,
        nullable=False,
    )

    published_by_user_id: Mapped[
        uuid.UUID
    ] = mapped_column(
        UUID(
            as_uuid=True
        ),
        nullable=False,
    )

    published_at: Mapped[
        datetime
    ] = mapped_column(
        DateTime(
            timezone=True
        ),
        nullable=False,
        default=utc_now,
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


__all__ = [
    "PayrollPayslip",
]