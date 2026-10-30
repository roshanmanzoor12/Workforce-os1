from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.tenant_base import TenantBase


def utc_now() -> datetime:
    return datetime.now(
        timezone.utc
    )


class Note(TenantBase):
    __tablename__ = "notes"

    __table_args__ = (
        Index(
            "ix_notes_owner_employee",
            "owner_employee_id",
        ),
        Index(
            "ix_notes_is_archived",
            "is_archived",
        ),
        Index(
            "ix_notes_is_pinned",
            "is_pinned",
        ),
    )

    # =====================================================
    # PRIMARY KEY
    # =====================================================

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # =====================================================
    # OWNERSHIP
    # =====================================================

    owner_employee_id: Mapped[
        uuid.UUID
    ] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "employees.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    # =====================================================
    # NOTE DATA
    # =====================================================

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text(),
        nullable=False,
        default="",
    )

    is_pinned: Mapped[
        bool
    ] = mapped_column(
        Boolean(),
        nullable=False,
        default=False,
    )

    is_archived: Mapped[
        bool
    ] = mapped_column(
        Boolean(),
        nullable=False,
        default=False,
    )

    # =====================================================
    # TIMESTAMPS
    # =====================================================

    created_at: Mapped[
        datetime
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    updated_at: Mapped[
        datetime
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


__all__ = [
    "Note",
]