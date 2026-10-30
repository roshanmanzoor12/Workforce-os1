from __future__ import annotations

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
    ForeignKey,
    Index,
    Integer,
    String,
    Time,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import (
    UUID,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.db.tenant_base import (
    TenantBase,
)


class SchedulePublicationDay(
    TenantBase
):
    """
    Immutable materialized schedule state for one employee/day
    inside one schedule publication.

    Source references are intentionally logical except
    publication_id.

    A later shift/holiday/exception edit must not rewrite
    historical published schedule state.
    """

    __tablename__ = (
        "schedule_publication_days"
    )

    __table_args__ = (
        UniqueConstraint(
            "publication_id",
            "employee_id",
            "schedule_date",
            name=(
                "uq_schedule_publication_day_"
                "publication_employee_date"
            ),
        ),
        Index(
            "ix_schedule_publication_days_"
            "employee_date",
            "employee_id",
            "schedule_date",
        ),
        Index(
            "ix_schedule_publication_days_"
            "publication",
            "publication_id",
        ),
    )

    id: Mapped[
        uuid.UUID
    ] = mapped_column(
        UUID(
            as_uuid=True
        ),
        primary_key=True,
        default=uuid.uuid4,
    )

    publication_id: Mapped[
        uuid.UUID
    ] = mapped_column(
        UUID(
            as_uuid=True
        ),
        ForeignKey(
            "schedule_publications.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    employee_id: Mapped[
        uuid.UUID
    ] = mapped_column(
        UUID(
            as_uuid=True
        ),
        nullable=False,
    )

    schedule_date: Mapped[
        date
    ] = mapped_column(
        Date(),
        nullable=False,
    )

    source: Mapped[
        str
    ] = mapped_column(
        String(64),
        nullable=False,
    )

    shift_id: Mapped[
        uuid.UUID | None
    ] = mapped_column(
        UUID(
            as_uuid=True
        ),
        nullable=True,
    )

    timezone: Mapped[
        str | None
    ] = mapped_column(
        String(64),
        nullable=True,
    )

    start_time: Mapped[
        time | None
    ] = mapped_column(
        Time(),
        nullable=True,
    )

    end_time: Mapped[
        time | None
    ] = mapped_column(
        Time(),
        nullable=True,
    )

    break_minutes: Mapped[
        int
    ] = mapped_column(
        Integer(),
        nullable=False,
        default=0,
    )

    scheduled_minutes: Mapped[
        int
    ] = mapped_column(
        Integer(),
        nullable=False,
        default=0,
    )

    payable_minutes: Mapped[
        int
    ] = mapped_column(
        Integer(),
        nullable=False,
        default=0,
    )

    is_working_day: Mapped[
        bool
    ] = mapped_column(
        Boolean(),
        nullable=False,
        default=False,
    )

    exception_id: Mapped[
        uuid.UUID | None
    ] = mapped_column(
        UUID(
            as_uuid=True
        ),
        nullable=True,
    )

    is_holiday: Mapped[
        bool
    ] = mapped_column(
        Boolean(),
        nullable=False,
        default=False,
    )

    holiday_id: Mapped[
        uuid.UUID | None
    ] = mapped_column(
        UUID(
            as_uuid=True
        ),
        nullable=True,
    )

    holiday_name: Mapped[
        str | None
    ] = mapped_column(
        String(160),
        nullable=True,
    )

    holiday_treatment: Mapped[
        str | None
    ] = mapped_column(
        String(20),
        nullable=True,
    )

    created_at: Mapped[
        datetime
    ] = mapped_column(
        DateTime(
            timezone=True
        ),
        nullable=False,
        default=datetime.utcnow,
    )


__all__ = [
    "SchedulePublicationDay",
]