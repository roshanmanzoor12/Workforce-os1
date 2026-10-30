from __future__ import annotations

import enum
import uuid
from datetime import (
    date,
    datetime,
    time,
)

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Time,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.db.tenant_base import TenantBase


# =========================================================
# ENUMS
# =========================================================


class ShiftAssignmentTargetType(
    str,
    enum.Enum,
):
    EMPLOYEE = "employee"
    TEAM = "team"


class ScheduleExceptionType(
    str,
    enum.Enum,
):
    OFF_DAY = "off_day"
    CUSTOM_SHIFT = "custom_shift"


class SchedulePublicationStatus(
    str,
    enum.Enum,
):
    DRAFT = "draft"
    PUBLISHED = "published"
    CANCELLED = "cancelled"


# =========================================================
# SHIFT TEMPLATE
# =========================================================


class ShiftTemplate(TenantBase):
    __tablename__ = "shift_templates"

    __table_args__ = (
        UniqueConstraint(
            "name",
            name="uq_shift_templates_name",
        ),
        Index(
            "ix_shift_templates_active",
            "is_active",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    timezone: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    start_time: Mapped[time] = mapped_column(
        Time(),
        nullable=False,
    )

    end_time: Mapped[time] = mapped_column(
        Time(),
        nullable=False,
    )

    break_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    standard_paid_minutes: Mapped[
        int | None
    ] = mapped_column(
        Integer,
        nullable=True,
    )

    grace_before_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    grace_after_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    overtime_after_minutes: Mapped[
        int | None
    ] = mapped_column(
        Integer,
        nullable=True,
    )

    is_overnight: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


# =========================================================
# WORKING DAYS
# =========================================================


class ShiftWorkingDay(TenantBase):
    __tablename__ = "shift_working_days"

    __table_args__ = (
        UniqueConstraint(
            "shift_id",
            "weekday",
            name=(
                "uq_shift_working_days_"
                "shift_weekday"
            ),
        ),
        Index(
            "ix_shift_working_days_shift",
            "shift_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    shift_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "shift_templates.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    # Python weekday format:
    # Monday = 0
    # Sunday = 6
    weekday: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    is_working_day: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )


# =========================================================
# SHIFT ASSIGNMENTS
# =========================================================


class ShiftAssignment(TenantBase):
    __tablename__ = "shift_assignments"

    __table_args__ = (
        Index(
            "ix_shift_assignments_target",
            "target_type",
            "target_id",
        ),
        Index(
            "ix_shift_assignments_effective",
            "effective_from",
            "effective_to",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    shift_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "shift_templates.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    target_type: Mapped[
        ShiftAssignmentTargetType
    ] = mapped_column(
        Enum(
            ShiftAssignmentTargetType,
            name="shift_assignment_target_type",
        ),
        nullable=False,
    )

    target_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )

    effective_from: Mapped[date] = mapped_column(
        Date(),
        nullable=False,
    )

    effective_to: Mapped[
        date | None
    ] = mapped_column(
        Date(),
        nullable=True,
    )

    priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


# =========================================================
# SCHEDULE EXCEPTIONS
# =========================================================


class ScheduleException(TenantBase):
    __tablename__ = "schedule_exceptions"

    __table_args__ = (
        UniqueConstraint(
            "employee_id",
            "exception_date",
            name=(
                "uq_schedule_exception_"
                "employee_date"
            ),
        ),
        Index(
            "ix_schedule_exceptions_date",
            "exception_date",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    exception_date: Mapped[date] = mapped_column(
        Date(),
        nullable=False,
    )

    exception_type: Mapped[
        ScheduleExceptionType
    ] = mapped_column(
        Enum(
            ScheduleExceptionType,
            name="schedule_exception_type",
        ),
        nullable=False,
    )

    custom_start_time: Mapped[
        time | None
    ] = mapped_column(
        Time(),
        nullable=True,
    )

    custom_end_time: Mapped[
        time | None
    ] = mapped_column(
        Time(),
        nullable=True,
    )

    break_minutes: Mapped[
        int | None
    ] = mapped_column(
        Integer,
        nullable=True,
    )

    reason: Mapped[
        str | None
    ] = mapped_column(
        String(500),
        nullable=True,
    )

    created_by_user_id: Mapped[
        uuid.UUID | None
    ] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


# =========================================================
# SCHEDULE PUBLICATION
# =========================================================


class SchedulePublication(TenantBase):
    __tablename__ = "schedule_publications"

    __table_args__ = (
        Index(
            "ix_schedule_publications_range",
            "period_start",
            "period_end",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    period_start: Mapped[date] = mapped_column(
        Date(),
        nullable=False,
    )

    period_end: Mapped[date] = mapped_column(
        Date(),
        nullable=False,
    )

    status: Mapped[
        SchedulePublicationStatus
    ] = mapped_column(
        Enum(
            SchedulePublicationStatus,
            name="schedule_publication_status",
        ),
        nullable=False,
        default=(
            SchedulePublicationStatus.PUBLISHED
        ),
    )

    published_by_user_id: Mapped[
        uuid.UUID | None
    ] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    published_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    note: Mapped[
        str | None
    ] = mapped_column(
        String(500),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )


__all__ = [
    "ShiftAssignmentTargetType",
    "ScheduleExceptionType",
    "SchedulePublicationStatus",
    "ShiftTemplate",
    "ShiftWorkingDay",
    "ShiftAssignment",
    "ScheduleException",
    "SchedulePublication",
]