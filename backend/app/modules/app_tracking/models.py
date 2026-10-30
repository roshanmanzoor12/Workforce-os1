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
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.tenant_base import TenantBase


APP_USAGE_STATUS_OPEN = "open"
APP_USAGE_STATUS_CLOSED = "closed"


class AppObservation(TenantBase):
    __tablename__ = "app_observations"

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

    app_key: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    process_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    executable_path: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    window_title: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    __table_args__ = (
        Index(
            "ix_app_observations_device_observed_at",
            "device_id",
            "observed_at",
        ),
        Index(
            "ix_app_observations_employee_observed_at",
            "employee_id",
            "observed_at",
        ),
        Index(
            "ix_app_observations_app_key_observed_at",
            "app_key",
            "observed_at",
        ),
    )


class AppUsageInterval(TenantBase):
    __tablename__ = "app_usage_intervals"

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

    app_key: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    process_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    executable_path: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    last_window_title: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=APP_USAGE_STATUS_OPEN,
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

    duration_seconds: Mapped[int] = mapped_column(
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
            name="ck_app_usage_intervals_status",
        ),
        CheckConstraint(
            "duration_seconds >= 0",
            name="ck_app_usage_intervals_duration_nonnegative",
        ),
        CheckConstraint(
            "ended_at IS NULL OR ended_at >= started_at",
            name="ck_app_usage_intervals_valid_time_range",
        ),
        Index(
            "ix_app_usage_intervals_device_started_at",
            "device_id",
            "started_at",
        ),
        Index(
            "ix_app_usage_intervals_employee_started_at",
            "employee_id",
            "started_at",
        ),
        Index(
            "ix_app_usage_intervals_app_key_started_at",
            "app_key",
            "started_at",
        ),
        Index(
            "uq_app_usage_one_open_per_device",
            "device_id",
            unique=True,
            postgresql_where=text(
                "status = 'open'"
            ),
        ),
    )


__all__ = [
    "APP_USAGE_STATUS_OPEN",
    "APP_USAGE_STATUS_CLOSED",
    "AppObservation",
    "AppUsageInterval",
]