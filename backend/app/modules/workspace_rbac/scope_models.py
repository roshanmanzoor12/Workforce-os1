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


SAVED_RESOURCE_SCOPE_TYPES = frozenset({
    "department",
    "team",
})


class WorkspaceMembershipScopeGrant(Base):
    """
    Explicit tenant-resource grants for a control-plane membership.

    Workspace ownership is derived from the referenced membership.
    Resource IDs belong to that workspace's tenant database and must
    be validated there before a grant is written.

    These rows grant resource visibility, not permissions.
    """

    __tablename__ = "workspace_membership_scope_grants"

    __table_args__ = (
        CheckConstraint(
            "scope_type IN ('department', 'team')",
            name="scope_type_supported",
        ),
        Index(
            "ix_membership_scope_grants_grantor",
            "granted_by_user_id",
        ),
    )

    membership_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "workspace_memberships.id",
            name="fk_membership_scope_grants_membership",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    scope_type: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
    )

    resource_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
    )

    granted_by_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "users.id",
            name="fk_membership_scope_grants_grantor",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


__all__ = [
    "SAVED_RESOURCE_SCOPE_TYPES",
    "WorkspaceMembershipScopeGrant",
]