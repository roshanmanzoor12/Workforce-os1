from __future__ import annotations

import enum
import uuid
from datetime import (
    date,
    datetime,
)

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    Index,
    String,
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


class HolidayTreatment(
    str,
    enum.Enum,
):
    PAID = "paid"
    UNPAID = "unpaid"


class Holiday(TenantBase):
    __tablename__ = "holidays"

    __table_args__ = (
        UniqueConstraint(
            "holiday_date",
            "name",
            name=(
                "uq_holidays_date_name"
            ),
        ),
        Index(
            "ix_holidays_date_active",
            "holiday_date",
            "is_active",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    holiday_date: Mapped[date] = mapped_column(
        Date(),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
    )

    treatment: Mapped[
        HolidayTreatment
    ] = mapped_column(
        Enum(
            HolidayTreatment,
            name="holiday_treatment",
        ),
        nullable=False,
        default=(
            HolidayTreatment.PAID
        ),
    )

    region: Mapped[
        str | None
    ] = mapped_column(
        String(120),
        nullable=True,
    )

    description: Mapped[
        str | None
    ] = mapped_column(
        String(500),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
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


__all__ = [
    "HolidayTreatment",
    "Holiday",
]