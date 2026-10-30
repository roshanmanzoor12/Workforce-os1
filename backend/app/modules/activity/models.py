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
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.tenant_base import TenantBase


__all__ = [
    "ACTIVITY_STATE_ACTIVE",
    "ACTIVITY_STATE_IDLE",
    "ActivityStateEvent",
]


ACTIVITY_STATE_ACTIVE = "active"
ACTIVITY_STATE_IDLE = "idle"


class ActivityStateEvent(TenantBase):
    """
    Tenant-local active/idle observation reported by an
    authenticated WorkforceOS Agent.

    This table stores only activity state metadata.

    It does NOT store:
    - keystrokes
    - typed text
    - clipboard contents
    - passwords
    - input content
    """

    __tablename__ = "activity_state_events"

    __table_args__ = (
        CheckConstraint(
            "state IN ('active', 'idle')",
            name="ck_activity_state_events_state",
        ),
        CheckConstraint(
            "idle_seconds >= 0",
            name="ck_activity_state_events_idle_seconds_nonnegative",
        ),
        Index(
            "ix_activity_state_events_device_observed_at",
            "device_id",
            "observed_at",
        ),
        Index(
            "ix_activity_state_events_employee_observed_at",
            "employee_id",
            "observed_at",
        ),
        Index(
            "ix_activity_state_events_received_at",
            "received_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "devices.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    employee_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "employees.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    state: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    idle_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    last_input_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )