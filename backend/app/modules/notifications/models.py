from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import (
    JSONB,
    UUID,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.db.base import Base


# =========================================================
# CONSTANTS
# =========================================================

NOTIFICATION_PRIORITY_LOW = "low"
NOTIFICATION_PRIORITY_NORMAL = "normal"
NOTIFICATION_PRIORITY_HIGH = "high"
NOTIFICATION_PRIORITY_URGENT = "urgent"


NOTIFICATION_PRIORITIES = frozenset(
    {
        NOTIFICATION_PRIORITY_LOW,
        NOTIFICATION_PRIORITY_NORMAL,
        NOTIFICATION_PRIORITY_HIGH,
        NOTIFICATION_PRIORITY_URGENT,
    }
)


# =========================================================
# NOTIFICATION
# =========================================================


class Notification(Base):
    __tablename__ = "notifications"

    __table_args__ = (
        Index(
            "ix_notif_user_created",
            "recipient_user_id",
            "created_at",
        ),
        Index(
            "ix_notif_user_read",
            "recipient_user_id",
            "read_at",
        ),
        Index(
            "ix_notif_entity",
            "entity_type",
            "entity_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    recipient_user_id: Mapped[
        uuid.UUID
    ] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    notification_type: Mapped[
        str
    ] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    body: Mapped[
        str | None
    ] = mapped_column(
        Text,
        nullable=True,
    )

    priority: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=NOTIFICATION_PRIORITY_NORMAL,
    )

    entity_type: Mapped[
        str | None
    ] = mapped_column(
        String(100),
        nullable=True,
    )

    entity_id: Mapped[
        uuid.UUID | None
    ] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    action_url: Mapped[
        str | None
    ] = mapped_column(
        String(1000),
        nullable=True,
    )

    payload: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    read_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(
            timezone=True
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


# =========================================================
# NOTIFICATION PREFERENCES
# =========================================================


class NotificationPreference(Base):
    __tablename__ = (
        "notification_preferences"
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            name="uq_notif_pref_user",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[
        uuid.UUID
    ] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    in_app_enabled: Mapped[
        bool
    ] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    email_enabled: Mapped[
        bool
    ] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    push_enabled: Mapped[
        bool
    ] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    sound_enabled: Mapped[
        bool
    ] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    digest_enabled: Mapped[
        bool
    ] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    digest_hour: Mapped[
        int
    ] = mapped_column(
        Integer,
        nullable=False,
        default=8,
    )

    muted_types: Mapped[
        list[str]
    ] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
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
    "NOTIFICATION_PRIORITY_LOW",
    "NOTIFICATION_PRIORITY_NORMAL",
    "NOTIFICATION_PRIORITY_HIGH",
    "NOTIFICATION_PRIORITY_URGENT",
    "NOTIFICATION_PRIORITIES",
    "Notification",
    "NotificationPreference",
]