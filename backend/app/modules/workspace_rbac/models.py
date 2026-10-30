from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    JSON,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.db.base import (
    Base,
    StandardModelMixin,
)


# =========================================================
# CUSTOM WORKSPACE ROLE
# =========================================================


class WorkspaceCustomRole(
    StandardModelMixin,
    Base,
):
    __tablename__ = "workspace_custom_roles"

    __table_args__ = (
        UniqueConstraint(
            "workspace_id",
            "role_key",
            name=(
                "uq_workspace_custom_roles_"
                "workspace_role_key"
            ),
        ),
        Index(
            "ix_workspace_custom_roles_"
            "workspace_id",
            "workspace_id",
        ),
    )

    workspace_id: Mapped[
        uuid.UUID
    ] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "workspaces.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    role_key: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    display_name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    description: Mapped[
        str | None
    ] = mapped_column(
        String(500),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_by_user_id: Mapped[
        uuid.UUID
    ] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )


# =========================================================
# ROLE PERMISSION
# =========================================================


class WorkspaceCustomRolePermission(
    StandardModelMixin,
    Base,
):
    __tablename__ = (
        "workspace_custom_role_permissions"
    )

    __table_args__ = (
        UniqueConstraint(
            "role_id",
            "permission_key",
            name=(
                "uq_workspace_custom_role_"
                "permissions_role_permission"
            ),
        ),
        Index(
            "ix_workspace_custom_role_"
            "permissions_role_id",
            "role_id",
        ),
    )

    role_id: Mapped[
        uuid.UUID
    ] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "workspace_custom_roles.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    permission_key: Mapped[
        str
    ] = mapped_column(
        String(150),
        nullable=False,
    )


class WorkspaceBuiltinRoleOverride(StandardModelMixin, Base):
    """Workspace-local replacement policy for a non-owner built-in role."""
    __tablename__ = "workspace_builtin_role_overrides"
    __table_args__ = (
        UniqueConstraint("workspace_id", "role_key", name="uq_builtin_role_override_workspace_key"),
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    role_key: Mapped[str] = mapped_column(String(64), nullable=False)
    permissions: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)


# =========================================================
# MEMBER MODERATION STATE
# =========================================================


class WorkspaceMembershipModeration(
    StandardModelMixin,
    Base,
):
    __tablename__ = (
        "workspace_membership_moderation"
    )

    __table_args__ = (
        UniqueConstraint(
            "membership_id",
            name=(
                "uq_workspace_membership_"
                "moderation_membership_id"
            ),
        ),
    )

    membership_id: Mapped[
        uuid.UUID
    ] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "workspace_memberships.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    is_banned: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    is_muted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    is_deafened: Mapped[
        bool
    ] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    is_hidden: Mapped[
        bool
    ] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    banned_at: Mapped[
        datetime | None
    ] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    banned_by_user_id: Mapped[
        uuid.UUID | None
    ] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )


__all__ = [
    "WorkspaceCustomRole",
    "WorkspaceCustomRolePermission",
    "WorkspaceMembershipModeration",
]