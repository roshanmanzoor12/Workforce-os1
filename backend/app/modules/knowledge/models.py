from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.db.tenant_base import TenantBase
from app.modules.knowledge.enums import (
    KnowledgeCategory,
    KnowledgeStatus,
    KnowledgeVisibility,
)


def utc_now() -> datetime:
    return datetime.now(
        timezone.utc
    )


class KnowledgeEntry(TenantBase):
    __tablename__ = "knowledge_entries"

    __table_args__ = (
        CheckConstraint(
            (
                "status IN "
                "('draft', 'published', 'archived')"
            ),
            name="ck_knowledge_entries_status",
        ),
        CheckConstraint(
            (
                "visibility IN "
                "('private', 'workspace')"
            ),
            name=(
                "ck_knowledge_entries_visibility"
            ),
        ),
        CheckConstraint(
            (
                "category IN "
                "('general', 'process', "
                "'reference', 'learning')"
            ),
            name=(
                "ck_knowledge_entries_category"
            ),
        ),
        Index(
            "ix_knowledge_entries_owner",
            "owner_employee_id",
        ),
        Index(
            "ix_knowledge_entries_status",
            "status",
        ),
        Index(
            "ix_knowledge_entries_visibility",
            "visibility",
        ),
        Index(
            "ix_knowledge_entries_category",
            "category",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

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

    title: Mapped[str] = mapped_column(
        String(250),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text(),
        nullable=False,
        default="",
    )

    category: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=KnowledgeCategory.GENERAL.value,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=KnowledgeStatus.DRAFT.value,
    )

    visibility: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=KnowledgeVisibility.PRIVATE.value,
    )

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
    "KnowledgeEntry",
]