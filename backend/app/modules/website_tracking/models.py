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
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.db.tenant_base import TenantBase


WEBSITE_USAGE_STATUS_OPEN = "open"
WEBSITE_USAGE_STATUS_CLOSED = "closed"


class WebsiteObservation(TenantBase):
    __tablename__ = "website_observations"

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

    browser_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    browser_process_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    domain: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    normalized_domain: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    page_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    page_title: Mapped[str | None] = mapped_column(
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
        server_default=text(
            "CURRENT_TIMESTAMP"
        ),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text(
            "CURRENT_TIMESTAMP"
        ),
    )

    __table_args__ = (
        Index(
            "ix_website_observations_device_observed_at",
            "device_id",
            "observed_at",
        ),
        Index(
            "ix_website_observations_employee_observed_at",
            "employee_id",
            "observed_at",
        ),
        Index(
            "ix_website_observations_domain_observed_at",
            "normalized_domain",
            "observed_at",
        ),
    )


class WebsiteUsageInterval(TenantBase):
    __tablename__ = "website_usage_intervals"

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

    browser_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    browser_process_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    domain: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    normalized_domain: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=WEBSITE_USAGE_STATUS_OPEN,
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

    last_page_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    last_page_title: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text(
            "CURRENT_TIMESTAMP"
        ),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text(
            "CURRENT_TIMESTAMP"
        ),
        onupdate=text(
            "CURRENT_TIMESTAMP"
        ),
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('open', 'closed')",
            name="ck_website_usage_intervals_status",
        ),
        CheckConstraint(
            "duration_seconds >= 0",
            name="ck_website_usage_intervals_duration_nonnegative",
        ),
        CheckConstraint(
            "ended_at IS NULL OR ended_at >= started_at",
            name="ck_website_usage_intervals_valid_time_range",
        ),
        Index(
            "ix_website_usage_intervals_device_started_at",
            "device_id",
            "started_at",
        ),
        Index(
            "ix_website_usage_intervals_employee_started_at",
            "employee_id",
            "started_at",
        ),
        Index(
            "ix_website_usage_intervals_domain_started_at",
            "normalized_domain",
            "started_at",
        ),
        Index(
            "uq_website_usage_one_open_per_device",
            "device_id",
            unique=True,
            postgresql_where=text(
                "status = 'open'"
            ),
        ),
    )


__all__ = [
    "WEBSITE_USAGE_STATUS_OPEN",
    "WEBSITE_USAGE_STATUS_CLOSED",
    "WebsiteObservation",
    "WebsiteUsageInterval",
]