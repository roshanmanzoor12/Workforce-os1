from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class WorkspaceMembershipRoleAssignment(Base):
    __tablename__ = "workspace_membership_role_assignments"

    __table_args__ = (
        CheckConstraint(
            "role_key <> 'owner'",
            name="ck_member_role_assignments_no_owner",
        ),
        CheckConstraint(
            """
            (
                role_key IN ('admin', 'manager', 'member', 'client')
                AND custom_role_id IS NULL
            )
            OR
            (
                role_key NOT IN (
                    'owner', 'admin', 'manager', 'member', 'client'
                )
                AND custom_role_id IS NOT NULL
            )
            """,
            name="ck_member_role_assignments_role_reference",
        ),
        Index(
            "ix_member_role_assignments_custom_role",
            "custom_role_id",
        ),
    )

    membership_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "workspace_memberships.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    role_key: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
    )

    custom_role_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "workspace_custom_roles.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )

    granted_by_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


__all__ = ["WorkspaceMembershipRoleAssignment"]