from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import (
    Date,
    ForeignKey,
    Index,
    JSON,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.tenant_base import (
    TenantBase,
    TenantStandardModelMixin,
)


class OnboardingRecord(
    TenantStandardModelMixin,
    TenantBase,
):
    __tablename__ = "employee_onboarding"

    __table_args__ = (
        Index(
            "ix_employee_onboarding_employee_id",
            "employee_id",
        ),
        Index(
            "ix_employee_onboarding_status",
            "status",
        ),
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "employees.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="pending",
        nullable=False,
    )

    start_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    completed_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    tasks: Mapped[list] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )


class OffboardingRecord(
    TenantStandardModelMixin,
    TenantBase,
):
    __tablename__ = "employee_offboarding"

    __table_args__ = (
        Index(
            "ix_employee_offboarding_employee_id",
            "employee_id",
        ),
        Index(
            "ix_employee_offboarding_status",
            "status",
        ),
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "employees.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="pending",
        nullable=False,
    )

    last_working_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    reason: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    tasks: Mapped[list] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )


__all__ = [
    "OnboardingRecord",
    "OffboardingRecord",
]