from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.db.base import Base


class WorkspaceChannelReadState(Base):
    __tablename__ = (
        "workspace_channel_read_states"
    )

    __table_args__ = (
        UniqueConstraint(
            "channel_id",
            "user_id",
            name=(
                "uq_workspace_channel_"
                "read_states_channel_user"
            ),
        ),
        Index(
            "ix_workspace_channel_"
            "read_states_user",
            "user_id",
        ),
        Index(
            "ix_workspace_channel_"
            "read_states_channel",
            "channel_id",
        ),
    )

    id: Mapped[
        uuid.UUID
    ] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    channel_id: Mapped[
        uuid.UUID
    ] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "workspace_channels.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    user_id: Mapped[
        uuid.UUID
    ] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    last_read_message_id: Mapped[
        uuid.UUID | None
    ] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "workspace_channel_messages.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    last_read_at: Mapped[
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


__all__ = [
    "WorkspaceChannelReadState",
]