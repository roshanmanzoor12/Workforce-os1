from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import CheckConstraint, Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.tenant_base import TenantBase, TenantStandardModelMixin


class Project(TenantStandardModelMixin, TenantBase):
    __tablename__ = "projects"

    __table_args__ = (
        CheckConstraint(
            "status IN ('planned', 'active', 'on_hold', "
            "'completed', 'archived')",
            name="ck_projects_status",
        ),
        CheckConstraint(
            "due_date IS NULL OR start_date IS NULL "
            "OR due_date >= start_date",
            name="ck_projects_dates",
        ),
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="planned", index=True
    )

    owner_employee_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    due_date: Mapped[date | None] = mapped_column(
        Date, nullable=True, index=True
    )


__all__ = ["Project"]