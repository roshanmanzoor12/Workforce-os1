from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Index,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.db.base import Base


VOICE_CALL_ACTIVE = "active"
VOICE_CALL_ENDED = "ended"

VOICE_PARTICIPANT_JOINED = "joined"
VOICE_PARTICIPANT_LEFT = "left"


class VoiceChannelCall(Base):
    __tablename__ = "voice_channel_calls"

    __table_args__ = (
        Index(
            "uq_voice_channel_calls_active_channel",
            "channel_id",
            unique=True,
            postgresql_where=text(
                "status = 'active'"
            ),
        ),
        Index(
            "ix_voice_channel_calls_channel",
            "channel_id",
            "created_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    channel_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        nullable=False,
    )

    created_by_user_id: Mapped[
        uuid.UUID
    ] = mapped_column(
        Uuid(as_uuid=True),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=VOICE_CALL_ACTIVE,
        server_default=VOICE_CALL_ACTIVE,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    ended_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class VoiceChannelParticipant(Base):
    __tablename__ = "voice_channel_participants"

    __table_args__ = (
        UniqueConstraint(
            "call_id",
            "user_id",
            name=(
                "uq_voice_channel_participants_"
                "call_user"
            ),
        ),
        Index(
            "ix_voice_channel_participants_call_state",
            "call_id",
            "state",
        ),
        Index(
            "ix_voice_channel_participants_user",
            "user_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    call_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        nullable=False,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        nullable=False,
    )

    state: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=VOICE_PARTICIPANT_JOINED,
        server_default=VOICE_PARTICIPANT_JOINED,
    )

    self_muted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    self_deafened: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    server_muted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    server_deafened: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    screen_sharing: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
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

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class VoiceChannelBan(Base):
    __tablename__ = "voice_channel_bans"

    __table_args__ = (
        UniqueConstraint(
            "channel_id",
            "user_id",
            name=(
                "uq_voice_channel_bans_"
                "channel_user"
            ),
        ),
        Index(
            "ix_voice_channel_bans_channel_active",
            "channel_id",
            "is_active",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    channel_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        nullable=False,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        nullable=False,
    )

    banned_by_user_id: Mapped[
        uuid.UUID
    ] = mapped_column(
        Uuid(as_uuid=True),
        nullable=False,
    )

    reason: Mapped[
        str | None
    ] = mapped_column(
        Text,
        nullable=True,
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

    lifted_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


__all__ = [
    "VOICE_CALL_ACTIVE",
    "VOICE_CALL_ENDED",
    "VOICE_PARTICIPANT_JOINED",
    "VOICE_PARTICIPANT_LEFT",
    "VoiceChannelCall",
    "VoiceChannelParticipant",
    "VoiceChannelBan",
]