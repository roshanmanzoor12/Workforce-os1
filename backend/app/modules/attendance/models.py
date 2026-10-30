from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.db.tenant_base import (
    TenantBase,
    TenantStandardModelMixin,
)
from app.modules.attendance.enums import (
    AttendanceEventType,
    AttendanceSource,
    AttendanceStatus,
)


class AttendanceRecord(
    TenantStandardModelMixin,
    TenantBase,
):
    __tablename__ = "attendance_records"

    __table_args__ = (
        UniqueConstraint(
            "employee_id",
            "attendance_date",
            name=(
                "uq_attendance_records_employee_date"
            ),
        ),
        CheckConstraint(
            (
                "status IN "
                "('present', 'absent', 'late', "
                "'half_day', 'on_leave', 'holiday')"
            ),
            name=(
                "ck_attendance_records_status"
            ),
        ),
        CheckConstraint(
            "worked_minutes >= 0",
            name=(
                "ck_attendance_records_worked_minutes"
            ),
        ),
        CheckConstraint(
            "break_minutes >= 0",
            name=(
                "ck_attendance_records_break_minutes"
            ),
        ),
        Index(
            "ix_attendance_records_employee_id",
            "employee_id",
        ),
        Index(
            "ix_attendance_records_attendance_date",
            "attendance_date",
        ),
        Index(
            "ix_attendance_records_status",
            "status",
        ),
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

    attendance_date: Mapped[
        date
    ] = mapped_column(
        Date,
        nullable=False,
    )

    status: Mapped[
        str
    ] = mapped_column(
        String(32),
        nullable=False,
        default=(
            AttendanceStatus.PRESENT.value
        ),
    )

    source: Mapped[
        str
    ] = mapped_column(
        String(32),
        nullable=False,
        default=(
            AttendanceSource.WEB.value
        ),
    )

    check_in_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    check_out_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    worked_minutes: Mapped[
        int
    ] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    break_minutes: Mapped[
        int
    ] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    notes: Mapped[
        str | None
    ] = mapped_column(
        Text,
        nullable=True,
    )

    created_by_user_id: Mapped[
        uuid.UUID | None
    ] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    updated_by_user_id: Mapped[
        uuid.UUID | None
    ] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    events: Mapped[
        list["AttendanceEvent"]
    ] = relationship(
        back_populates="attendance_record",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="AttendanceEvent.occurred_at",
    )


class AttendanceEvent(
    TenantStandardModelMixin,
    TenantBase,
):
    __tablename__ = "attendance_events"

    __table_args__ = (
        CheckConstraint(
            (
                "event_type IN "
                "('check_in', 'check_out', "
                "'break_start', 'break_end')"
            ),
            name="ck_attendance_events_type",
        ),
        CheckConstraint(
            (
                "source IN "
                "('manual', 'web', 'desktop_agent', "
                "'import', 'system')"
            ),
            name="ck_attendance_events_source",
        ),
        Index(
            "ix_attendance_events_record_id",
            "attendance_record_id",
        ),
        Index(
            "ix_attendance_events_employee_id",
            "employee_id",
        ),
        Index(
            "ix_attendance_events_occurred_at",
            "occurred_at",
        ),
    )

    attendance_record_id: Mapped[
        uuid.UUID
    ] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "attendance_records.id",
            ondelete="CASCADE",
        ),
        nullable=False,
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

    event_type: Mapped[
        str
    ] = mapped_column(
        String(32),
        nullable=False,
    )

    source: Mapped[
        str
    ] = mapped_column(
        String(32),
        nullable=False,
        default=(
            AttendanceSource.WEB.value
        ),
    )

    occurred_at: Mapped[
        datetime
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    actor_user_id: Mapped[
        uuid.UUID | None
    ] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    notes: Mapped[
        str | None
    ] = mapped_column(
        Text,
        nullable=True,
    )

    attendance_record: Mapped[
        AttendanceRecord
    ] = relationship(
        back_populates="events",
    )


# Compatibility alias for code introduced during Phase 11.7.
AttendanceDay = AttendanceRecord


__all__ = [
    "AttendanceRecord",
    "AttendanceDay",
    "AttendanceEvent",
    "AttendanceStatus",
    "AttendanceEventType",
    "AttendanceSource",
]