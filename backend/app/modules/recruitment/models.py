from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.tenant_base import (
    TenantBase,
    TenantStandardModelMixin,
)


class JobStatus(StrEnum):
    DRAFT = "draft"
    OPEN = "open"
    PAUSED = "paused"
    CLOSED = "closed"


class CandidateStatus(StrEnum):
    NEW = "new"
    SCREENING = "screening"
    INTERVIEW = "interview"
    OFFER = "offer"
    HIRED = "hired"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class InterviewStatus(StrEnum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class JobPosting(
    TenantStandardModelMixin,
    TenantBase,
):
    __tablename__ = "job_postings"

    __table_args__ = (
        Index("ix_job_postings_status", "status"),
        Index("ix_job_postings_department_id", "department_id"),
    )

    title: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "departments.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    location: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default=JobStatus.DRAFT.value,
        nullable=False,
    )

    employment_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    closing_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class Candidate(
    TenantStandardModelMixin,
    TenantBase,
):
    __tablename__ = "candidates"

    __table_args__ = (
        Index("ix_candidates_job_id", "job_id"),
        Index("ix_candidates_status", "status"),
        Index("ix_candidates_email", "email"),
    )

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "job_postings.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    phone: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
    )

    resume_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default=CandidateStatus.NEW.value,
        nullable=False,
    )


class Interview(
    TenantStandardModelMixin,
    TenantBase,
):
    __tablename__ = "recruitment_interviews"

    __table_args__ = (
        Index("ix_recruitment_interviews_candidate_id", "candidate_id"),
        Index("ix_recruitment_interviews_starts_at", "starts_at"),
    )

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "candidates.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    interviewer_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default=InterviewStatus.SCHEDULED.value,
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )


__all__ = [
    "JobStatus",
    "CandidateStatus",
    "InterviewStatus",
    "JobPosting",
    "Candidate",
    "Interview",
]