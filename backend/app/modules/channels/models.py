from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.db.base import Base

from .enums import (
    WorkspaceChannelMessageType,
    WorkspaceChannelRole,
    WorkspaceChannelType,
)


def enum_values(
    enum_class,
) -> list[str]:
    return [
        member.value
        for member in enum_class
    ]


class WorkspaceChannel(Base):
    __tablename__ = "workspace_channels"

    __table_args__ = (
        UniqueConstraint(
            "workspace_id",
            "slug",
            name="uq_workspace_channels_workspace_slug",
        ),
        Index(
            "ix_workspace_channels_workspace_active",
            "workspace_id",
            "is_active",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "workspaces.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    slug: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    channel_type: Mapped[
        WorkspaceChannelType
    ] = mapped_column(
        Enum(
            WorkspaceChannelType,
            name="workspace_channel_type",
            native_enum=False,
            values_callable=enum_values,
        ),
        nullable=False,
        default=WorkspaceChannelType.TEXT,
    )

    created_by_user_id: Mapped[
        uuid.UUID
    ] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
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


class WorkspaceChannelMember(Base):
    __tablename__ = "workspace_channel_members"

    __table_args__ = (
        UniqueConstraint(
            "channel_id",
            "user_id",
            name="uq_workspace_channel_members_channel_user",
        ),
        Index(
            "ix_workspace_channel_members_user_active",
            "user_id",
            "left_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    channel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "workspace_channels.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    role: Mapped[
        WorkspaceChannelRole
    ] = mapped_column(
        Enum(
            WorkspaceChannelRole,
            name="workspace_channel_role",
            native_enum=False,
            values_callable=enum_values,
        ),
        nullable=False,
        default=WorkspaceChannelRole.MEMBER,
    )

    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    left_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class WorkspaceChannelMessage(Base):
    __tablename__ = "workspace_channel_messages"

    __table_args__ = (
        Index(
            "ix_workspace_channel_messages_channel_created",
            "channel_id",
            "created_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    channel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "workspace_channels.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    sender_user_id: Mapped[
        uuid.UUID | None
    ] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    message_type: Mapped[
        WorkspaceChannelMessageType
    ] = mapped_column(
        Enum(
            WorkspaceChannelMessageType,
            name="workspace_channel_message_type",
            native_enum=False,
            values_callable=enum_values,
        ),
        nullable=False,
        default=(
            WorkspaceChannelMessageType.TEXT
        ),
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    edited_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    deleted_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


__all__ = [
    "WorkspaceChannel",
    "WorkspaceChannelMember",
    "WorkspaceChannelMessage",
]