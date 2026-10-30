from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Integer,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.db.base import Base


class MonitoringAdminPolicy(Base):
    __tablename__ = (
        "monitoring_admin_policies"
    )

    __table_args__ = (
        CheckConstraint(
            (
                "screenshot_interval_seconds "
                ">= 1"
            ),
            name=(
                "ck_monitoring_admin_policy_"
                "screenshot_interval_seconds"
            ),
        ),

        CheckConstraint(
            "screenshot_retention_days >= 1 "
            "AND screenshot_retention_days <= 3650",
            name=(
                "ck_monitoring_admin_policy_"
                "screenshot_retention_days"
            ),
        ),

        CheckConstraint(
            "live_session_max_minutes >= 1 "
            "AND live_session_max_minutes <= 480",
            name=(
                "ck_monitoring_admin_policy_"
                "live_session_max_minutes"
            ),
        ),
    )

    id: Mapped[
        uuid.UUID
    ] = mapped_column(
        Uuid(
            as_uuid=True
        ),
        primary_key=True,
        default=uuid.uuid4,
    )

    policy_key: Mapped[
        str
    ] = mapped_column(
        String(
            64
        ),
        nullable=False,
        unique=True,
        default="default",
        server_default="default",
    )

    monitoring_enabled: Mapped[
        bool
    ] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    screenshots_enabled: Mapped[
        bool
    ] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    live_screen_enabled: Mapped[
        bool
    ] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    screen_share_enabled: Mapped[
        bool
    ] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    disclosure_required: Mapped[
        bool
    ] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    explicit_live_consent_required: Mapped[
        bool
    ] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    visible_live_indicator_required: Mapped[
        bool
    ] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    screenshot_interval_seconds: Mapped[
        int
    ] = mapped_column(
        Integer,
        nullable=False,
        default=300,
        server_default="300",
    )

    screenshot_retention_days: Mapped[
        int
    ] = mapped_column(
        Integer,
        nullable=False,
        default=30,
        server_default="30",
    )

    live_session_max_minutes: Mapped[
        int
    ] = mapped_column(
        Integer,
        nullable=False,
        default=60,
        server_default="60",
    )

    policy_version: Mapped[
        int
    ] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )

    policy_notice: Mapped[
        str | None
    ] = mapped_column(
        Text,
        nullable=True,
    )

    updated_by_user_id: Mapped[
        uuid.UUID | None
    ] = mapped_column(
        Uuid(
            as_uuid=True
        ),
        nullable=True,
    )

    created_at: Mapped[
        datetime
    ] = mapped_column(
        DateTime(
            timezone=True
        ),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[
        datetime
    ] = mapped_column(
        DateTime(
            timezone=True
        ),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


__all__ = [
    "MonitoringAdminPolicy",
]