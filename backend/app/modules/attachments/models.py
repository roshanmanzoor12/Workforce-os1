from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AttachmentScope(str, enum.Enum):
    CONVERSATION = "CONVERSATION"
    CHANNEL = "CHANNEL"
    NOTE = "NOTE"


class AttachmentStatus(str, enum.Enum):
    PENDING = "PENDING"
    READY = "READY"
    DELETED = "DELETED"
    FAILED = "FAILED"


class AttachmentKind(str, enum.Enum):
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    FILE = "FILE"


class Attachment(Base):
    __tablename__ = "attachments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    scope: Mapped[AttachmentScope] = mapped_column(
        SqlEnum(
            AttachmentScope,
            name="attachment_scope",
            native_enum=True,
        ),
        nullable=False,
    )

    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    channel_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    personal_note_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "personal_notes.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
        index=True,
    )

    message_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    kind: Mapped[AttachmentKind] = mapped_column(
        SqlEnum(
            AttachmentKind,
            name="attachment_kind",
            native_enum=True,
        ),
        nullable=False,
    )

    status: Mapped[AttachmentStatus] = mapped_column(
        SqlEnum(
            AttachmentStatus,
            name="attachment_status",
            native_enum=True,
        ),
        nullable=False,
        default=AttachmentStatus.PENDING,
        index=True,
    )

    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    content_type: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    size_bytes: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    bucket_name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )

    object_key: Mapped[str] = mapped_column(
        String(1024),
        nullable=False,
        unique=True,
    )

    checksum_sha256: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    failure_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
    )

    ready_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


Index(
    "ix_attachments_conversation_created",
    Attachment.conversation_id,
    Attachment.created_at,
)

Index(
    "ix_attachments_channel_created",
    Attachment.channel_id,
    Attachment.created_at,
)

Index(
    "ix_attachments_owner_created",
    Attachment.owner_user_id,
    Attachment.created_at,
)