from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.tenant_base import TenantBase
from app.modules.goals.enums import (
    GoalPriority,
    GoalStatus,
)


def utc_now() -> datetime:
    return datetime.now(
        timezone.utc
    )


class Goal(TenantBase):
    __tablename__ = "goals"

    __table_args__ = (
        CheckConstraint(
            (
                "status IN "
                "('active', 'completed', "
                "'cancelled', 'archived')"
            ),
            name="ck_goals_status",
        ),
        CheckConstraint(
            (
                "priority IN "
                "('low', 'medium', 'high')"
            ),
            name="ck_goals_priority",
        ),
        CheckConstraint(
            (
                "progress_percent >= 0 "
                "AND progress_percent <= 100"
            ),
            name="ck_goals_progress_percent",
        ),
        Index(
            "ix_goals_owner_employee",
            "owner_employee_id",
        ),
        Index(
            "ix_goals_status",
            "status",
        ),
        Index(
            "ix_goals_due_date",
            "due_date",
        ),
    )

    # =====================================================
    # PRIMARY KEY
    # =====================================================

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # =====================================================
    # OWNERSHIP
    # =====================================================

    owner_employee_id: Mapped[
        uuid.UUID
    ] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "employees.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    # =====================================================
    # GOAL DATA
    # =====================================================

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[
        str | None
    ] = mapped_column(
        Text(),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=GoalStatus.ACTIVE.value,
    )

    priority: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=GoalPriority.MEDIUM.value,
    )

    progress_percent: Mapped[int] = (
        mapped_column(
            Integer(),
            nullable=False,
            default=0,
        )
    )

    start_date: Mapped[
        date | None
    ] = mapped_column(
        Date(),
        nullable=True,
    )

    due_date: Mapped[
        date | None
    ] = mapped_column(
        Date(),
        nullable=True,
    )

    completed_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # =====================================================
    # TIMESTAMPS
    # =====================================================

    created_at: Mapped[
        datetime
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    updated_at: Mapped[
        datetime
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


__all__ = [
    "Goal",
]