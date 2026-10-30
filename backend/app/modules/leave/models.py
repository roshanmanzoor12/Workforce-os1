from __future__ import annotations

import enum
import uuid
from datetime import (
    date,
    datetime,
)
from decimal import Decimal

from sqlalchemy import (
    Boolean,
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
    UUID,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.db.tenant_base import (
    TenantBase,
)


class LeaveRequestStatus(
    str,
    enum.Enum,
):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class LeaveType(
    TenantBase
):
    __tablename__ = "leave_types"

    __table_args__ = (
        UniqueConstraint(
            "code",
            name="uq_leave_types_code",
        ),
        Index(
            "ix_leave_types_active",
            "is_active",
        ),
    )

    id: Mapped[
        uuid.UUID
    ] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    description: Mapped[
        str | None
    ] = mapped_column(
        Text(),
        nullable=True,
    )

    is_paid: Mapped[bool] = mapped_column(
        Boolean(),
        nullable=False,
        default=True,
    )

    requires_approval: Mapped[
        bool
    ] = mapped_column(
        Boolean(),
        nullable=False,
        default=True,
    )

    is_active: Mapped[
        bool
    ] = mapped_column(
        Boolean(),
        nullable=False,
        default=True,
    )

    created_at: Mapped[
        datetime
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at: Mapped[
        datetime
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


class LeavePolicy(
    TenantBase
):
    __tablename__ = "leave_policies"

    __table_args__ = (
        UniqueConstraint(
            "leave_type_id",
            name=(
                "uq_leave_policies_"
                "leave_type"
            ),
        ),
    )

    id: Mapped[
        uuid.UUID
    ] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    leave_type_id: Mapped[
        uuid.UUID
    ] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "leave_types.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    annual_allowance_days: Mapped[
        Decimal
    ] = mapped_column(
        Numeric(
            8,
            2,
        ),
        nullable=False,
        default=Decimal("0"),
    )

    carry_forward_days: Mapped[
        Decimal
    ] = mapped_column(
        Numeric(
            8,
            2,
        ),
        nullable=False,
        default=Decimal("0"),
    )

    minimum_notice_days: Mapped[
        int
    ] = mapped_column(
        Integer(),
        nullable=False,
        default=0,
    )

    allow_negative_balance: Mapped[
        bool
    ] = mapped_column(
        Boolean(),
        nullable=False,
        default=False,
    )

    is_active: Mapped[
        bool
    ] = mapped_column(
        Boolean(),
        nullable=False,
        default=True,
    )

    created_at: Mapped[
        datetime
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at: Mapped[
        datetime
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


class LeaveBalance(
    TenantBase
):
    __tablename__ = "leave_balances"

    __table_args__ = (
        UniqueConstraint(
            "employee_id",
            "leave_type_id",
            "balance_year",
            name=(
                "uq_leave_balances_"
                "employee_type_year"
            ),
        ),
        Index(
            "ix_leave_balances_employee_year",
            "employee_id",
            "balance_year",
        ),
    )

    id: Mapped[
        uuid.UUID
    ] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    employee_id: Mapped[
        uuid.UUID
    ] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "employees.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    leave_type_id: Mapped[
        uuid.UUID
    ] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "leave_types.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    balance_year: Mapped[
        int
    ] = mapped_column(
        Integer(),
        nullable=False,
    )

    allocated_days: Mapped[
        Decimal
    ] = mapped_column(
        Numeric(
            8,
            2,
        ),
        nullable=False,
        default=Decimal("0"),
    )

    carried_forward_days: Mapped[
        Decimal
    ] = mapped_column(
        Numeric(
            8,
            2,
        ),
        nullable=False,
        default=Decimal("0"),
    )

    adjustment_days: Mapped[
        Decimal
    ] = mapped_column(
        Numeric(
            8,
            2,
        ),
        nullable=False,
        default=Decimal("0"),
    )

    used_days: Mapped[
        Decimal
    ] = mapped_column(
        Numeric(
            8,
            2,
        ),
        nullable=False,
        default=Decimal("0"),
    )

    pending_days: Mapped[
        Decimal
    ] = mapped_column(
        Numeric(
            8,
            2,
        ),
        nullable=False,
        default=Decimal("0"),
    )

    updated_by_user_id: Mapped[
        uuid.UUID | None
    ] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    created_at: Mapped[
        datetime
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at: Mapped[
        datetime
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    @property
    def available_days(
        self,
    ) -> Decimal:
        return (
            self.allocated_days
            + self.carried_forward_days
            + self.adjustment_days
            - self.used_days
            - self.pending_days
        )


class LeaveRequest(
    TenantBase
):
    __tablename__ = "leave_requests"

    __table_args__ = (
        Index(
            "ix_leave_requests_"
            "employee_dates",
            "employee_id",
            "start_date",
            "end_date",
        ),
        Index(
            "ix_leave_requests_status",
            "status",
        ),
    )

    id: Mapped[
        uuid.UUID
    ] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    employee_id: Mapped[
        uuid.UUID
    ] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "employees.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    leave_type_id: Mapped[
        uuid.UUID
    ] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "leave_types.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    start_date: Mapped[
        date
    ] = mapped_column(
        Date(),
        nullable=False,
    )

    end_date: Mapped[
        date
    ] = mapped_column(
        Date(),
        nullable=False,
    )

    requested_days: Mapped[
        Decimal
    ] = mapped_column(
        Numeric(
            8,
            2,
        ),
        nullable=False,
    )

    status: Mapped[
        LeaveRequestStatus
    ] = mapped_column(
        Enum(
            LeaveRequestStatus,
            name=(
                "leave_request_status"
            ),
        ),
        nullable=False,
        default=(
            LeaveRequestStatus.PENDING
        ),
    )

    reason: Mapped[
        str | None
    ] = mapped_column(
        Text(),
        nullable=True,
    )

    decision_note: Mapped[
        str | None
    ] = mapped_column(
        Text(),
        nullable=True,
    )

    created_by_user_id: Mapped[
        uuid.UUID | None
    ] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    reviewed_by_user_id: Mapped[
        uuid.UUID | None
    ] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    reviewed_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[
        datetime
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at: Mapped[
        datetime
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


__all__ = [
    "LeaveRequestStatus",
    "LeaveType",
    "LeavePolicy",
    "LeaveBalance",
    "LeaveRequest",
]