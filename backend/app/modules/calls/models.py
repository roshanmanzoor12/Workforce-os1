from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum as SqlEnum,
    Index,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.db.base import Base
from app.modules.calls.enums import (
    CallKind,
    CallParticipantState,
    CallScope,
    CallStatus,
    ScreenShareState,
)


def enum_values(enum_class) -> list[str]:
    return [
        member.value
        for member in enum_class
    ]


class RealtimeCall(Base):
    __tablename__ = "realtime_calls"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    scope: Mapped[CallScope] = mapped_column(
        SqlEnum(
            CallScope,
            name="call_scope",
            values_callable=enum_values,
        ),
        nullable=False,
    )

    conversation_id: Mapped[
        uuid.UUID | None
    ] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    channel_id: Mapped[
        uuid.UUID | None
    ] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    started_by_user_id: Mapped[
        uuid.UUID
    ] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    kind: Mapped[CallKind] = mapped_column(
        SqlEnum(
            CallKind,
            name="call_kind",
            values_callable=enum_values,
        ),
        nullable=False,
    )

    status: Mapped[
        CallStatus
    ] = mapped_column(
        SqlEnum(
            CallStatus,
            name="call_status",
            values_callable=enum_values,
        ),
        nullable=False,
        default=CallStatus.RINGING,
        index=True,
    )

    created_at: Mapped[
        datetime
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    started_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    ended_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    ended_by_user_id: Mapped[
        uuid.UUID | None
    ] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    __table_args__ = (
        CheckConstraint(
            "("
            "scope = 'CONVERSATION' "
            "AND conversation_id IS NOT NULL "
            "AND channel_id IS NULL"
            ") OR ("
            "scope = 'CHANNEL' "
            "AND channel_id IS NOT NULL "
            "AND conversation_id IS NULL"
            ")",
            name="ck_realtime_call_scope_target",
        ),
        Index(
            "ix_realtime_calls_conversation_status",
            "conversation_id",
            "status",
        ),
        Index(
            "ix_realtime_calls_channel_status",
            "channel_id",
            "status",
        ),
    )


class RealtimeCallParticipant(Base):
    __tablename__ = "realtime_call_participants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    call_id: Mapped[
        uuid.UUID
    ] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    user_id: Mapped[
        uuid.UUID
    ] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    state: Mapped[
        CallParticipantState
    ] = mapped_column(
        SqlEnum(
            CallParticipantState,
            name="call_participant_state",
            values_callable=enum_values,
        ),
        nullable=False,
        default=(
            CallParticipantState.INVITED
        ),
        index=True,
    )

    microphone_enabled: Mapped[
        bool
    ] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    camera_enabled: Mapped[
        bool
    ] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    screen_share_state: Mapped[
        ScreenShareState
    ] = mapped_column(
        SqlEnum(
            ScreenShareState,
            name="screen_share_state",
            values_callable=enum_values,
        ),
        nullable=False,
        default=ScreenShareState.STOPPED,
    )

    joined_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    left_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    connection_id: Mapped[
        str | None
    ] = mapped_column(
        String(255),
        nullable=True,
    )

    last_heartbeat_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    created_at: Mapped[
        datetime
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        UniqueConstraint(
            "call_id",
            "user_id",
            name=(
                "uq_realtime_call_participant_user"
            ),
        ),
        Index(
            "ix_realtime_call_participants_call_state",
            "call_id",
            "state",
        ),
    )