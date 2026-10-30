from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Index,
    String,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.db.base import Base


DEVICE_STATUS_ONLINE = "online"
DEVICE_STATUS_OFFLINE = "offline"
DEVICE_STATUS_DISABLED = "disabled"


class DesktopAgentDevice(Base):
    __tablename__ = "desktop_agent_devices"

    __table_args__ = (
        Index(
            "ix_desktop_agent_devices_user",
            "user_id",
        ),
        Index(
            "ix_desktop_agent_devices_employee",
            "employee_id",
        ),
        Index(
            "ix_desktop_agent_devices_status_seen",
            "status",
            "last_seen_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Logical global-user UUID.
    #
    # Tenant DB deliberately has no FK to the
    # control database.
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        nullable=False,
    )

    # Logical tenant Employee UUID.
    employee_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        nullable=False,
    )

    # Stable client-generated installation identity.
    #
    # This is NOT an authentication secret.
    installation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        nullable=False,
        unique=True,
    )

    device_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    platform: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    os_version: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    agent_version: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=DEVICE_STATUS_ONLINE,
        server_default=DEVICE_STATUS_ONLINE,
    )

    is_disabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    consent_version: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    consent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    capabilities: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    last_ip_address: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


__all__ = [
    "DEVICE_STATUS_ONLINE",
    "DEVICE_STATUS_OFFLINE",
    "DEVICE_STATUS_DISABLED",
    "DesktopAgentDevice",
]