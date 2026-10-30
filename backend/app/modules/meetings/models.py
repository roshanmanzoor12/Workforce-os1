from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.db.tenant_base import (
    TenantBase,
    TenantStandardModelMixin,
)
from app.modules.meetings.enums import (
    MeetingParticipantRole,
    MeetingParticipantStatus,
    MeetingStatus,
    MeetingType,
)


class Meeting(
    TenantStandardModelMixin,
    TenantBase,
):
    """
    Tenant-scoped scheduled meeting.

    workspace_id is intentionally absent because physical tenant
    database isolation already determines the workspace.
    """

    __tablename__ = "meetings"

    __table_args__ = (
        CheckConstraint(
            (
                "status IN "
                "('scheduled', 'active', "
                "'completed', 'cancelled')"
            ),
            name="ck_meetings_status",
        ),
        CheckConstraint(
            (
                "meeting_type IN "
                "('video', 'voice', 'in_person')"
            ),
            name="ck_meetings_type",
        ),
        CheckConstraint(
            (
                "scheduled_end_at IS NULL "
                "OR scheduled_end_at > scheduled_start_at"
            ),
            name="ck_meetings_end_after_start",
        ),
        Index(
            "ix_meetings_status",
            "status",
        ),
        Index(
            "ix_meetings_start",
            "scheduled_start_at",
        ),
        Index(
            "ix_meetings_created_by_user",
            "created_by_user_id",
        ),
    )

    title: Mapped[
        str
    ] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[
        str | None
    ] = mapped_column(
        Text,
        nullable=True,
    )

    meeting_type: Mapped[
        str
    ] = mapped_column(
        String(32),
        nullable=False,
        default=MeetingType.VIDEO.value,
    )

    status: Mapped[
        str
    ] = mapped_column(
        String(32),
        nullable=False,
        default=MeetingStatus.SCHEDULED.value,
    )

    scheduled_start_at: Mapped[
        datetime
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    scheduled_end_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
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

    location: Mapped[
        str | None
    ] = mapped_column(
        String(500),
        nullable=True,
    )

    created_by_user_id: Mapped[
        uuid.UUID
    ] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )

    participants: Mapped[
        list["MeetingParticipant"]
    ] = relationship(
        back_populates="meeting",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class MeetingParticipant(
    TenantStandardModelMixin,
    TenantBase,
):
    __tablename__ = "meeting_participants"

    __table_args__ = (
        UniqueConstraint(
            "meeting_id",
            "employee_id",
            name=(
                "uq_meeting_participants_"
                "meeting_employee"
            ),
        ),
        CheckConstraint(
            (
                "participant_role IN "
                "('organizer', 'participant')"
            ),
            name=(
                "ck_meeting_participants_role"
            ),
        ),
        CheckConstraint(
            (
                "status IN "
                "('invited', 'accepted', 'declined')"
            ),
            name=(
                "ck_meeting_participants_status"
            ),
        ),
        Index(
            "ix_meeting_participants_meeting",
            "meeting_id",
        ),
        Index(
            "ix_meeting_participants_employee",
            "employee_id",
        ),
    )

    meeting_id: Mapped[
        uuid.UUID
    ] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "meetings.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    employee_id: Mapped[
        uuid.UUID
    ] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "employees.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    participant_role: Mapped[
        str
    ] = mapped_column(
        String(32),
        nullable=False,
        default=(
            MeetingParticipantRole
            .PARTICIPANT
            .value
        ),
    )

    status: Mapped[
        str
    ] = mapped_column(
        String(32),
        nullable=False,
        default=(
            MeetingParticipantStatus
            .INVITED
            .value
        ),
    )

    meeting: Mapped[
        Meeting
    ] = relationship(
        back_populates="participants",
    )


__all__ = [
    "Meeting",
    "MeetingParticipant",
]