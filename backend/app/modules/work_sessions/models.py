from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.tenant_base import TenantBase


WORK_SESSION_STATUS_OPEN = "open"
WORK_SESSION_STATUS_CLOSED = "closed"

WORK_SESSION_STATE_ACTIVE = "active"
WORK_SESSION_STATE_IDLE = "idle"


class WorkSession(TenantBase):
    __tablename__ = "work_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    device_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "devices.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    employee_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "employees.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=WORK_SESSION_STATUS_OPEN,
    )

    current_state: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=WORK_SESSION_STATE_IDLE,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    last_observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    active_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    idle_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('open', 'closed')",
            name="ck_work_sessions_status",
        ),
        CheckConstraint(
            "current_state IN ('active', 'idle')",
            name="ck_work_sessions_current_state",
        ),
        CheckConstraint(
            "active_seconds >= 0",
            name="ck_work_sessions_active_seconds_nonnegative",
        ),
        CheckConstraint(
            "idle_seconds >= 0",
            name="ck_work_sessions_idle_seconds_nonnegative",
        ),
        CheckConstraint(
            "ended_at IS NULL OR ended_at >= started_at",
            name="ck_work_sessions_valid_time_range",
        ),
        Index(
            "ix_work_sessions_device_started_at",
            "device_id",
            "started_at",
        ),
        Index(
            "ix_work_sessions_employee_started_at",
            "employee_id",
            "started_at",
        ),
        Index(
            "ix_work_sessions_status_last_observed_at",
            "status",
            "last_observed_at",
        ),
        Index(
            "uq_work_sessions_one_open_per_device",
            "device_id",
            unique=True,
            postgresql_where=text(
                "status = 'open'"
            ),
        ),
    )

    @property
    def total_seconds(self) -> int:
        return (
            self.active_seconds
            + self.idle_seconds
        )


__all__ = [
    "WORK_SESSION_STATUS_OPEN",
    "WORK_SESSION_STATUS_CLOSED",
    "WORK_SESSION_STATE_ACTIVE",
    "WORK_SESSION_STATE_IDLE",
    "WorkSession",
]