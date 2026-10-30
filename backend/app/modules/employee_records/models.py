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


class EmployeeRecord(
    TenantStandardModelMixin,
    TenantBase,
):
    __tablename__ = "employee_records"

    __table_args__ = (
        Index(
            "ix_employee_records_employee_id",
            "employee_id",
        ),
        Index(
            "ix_employee_records_record_type",
            "record_type",
        ),
        Index(
            "ix_employee_records_effective_date",
            "effective_date",
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

    record_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    value: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    effective_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    metadata_json: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )


__all__ = ["EmployeeRecord"]