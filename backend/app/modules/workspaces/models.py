from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
    synonym,
)

from app.db.base import Base, StandardModelMixin
from app.modules.auth.models import User


WORKSPACE_STATUS_PROVISIONING = "provisioning"
WORKSPACE_STATUS_READY = "ready"
WORKSPACE_STATUS_FAILED = "failed"
WORKSPACE_STATUS_SUSPENDED = "suspended"
WORKSPACE_STATUS_ARCHIVED = "archived"

MEMBERSHIP_STATUS_ACTIVE = "active"
MEMBERSHIP_STATUS_INVITED = "invited"
MEMBERSHIP_STATUS_SUSPENDED = "suspended"
MEMBERSHIP_STATUS_REMOVED = "removed"

WORKSPACE_ROLE_OWNER = "owner"
WORKSPACE_ROLE_ADMIN = "admin"
WORKSPACE_ROLE_MEMBER = "member"

TENANT_STATUS_PENDING = "pending"
TENANT_STATUS_PROVISIONING = "provisioning"
TENANT_STATUS_READY = "ready"
TENANT_STATUS_FAILED = "failed"
TENANT_STATUS_SUSPENDED = "suspended"
TENANT_STATUS_DECOMMISSIONED = "decommissioned"

INVITATION_STATUS_PENDING = "pending"
INVITATION_STATUS_ACCEPTED = "accepted"
INVITATION_STATUS_DECLINED = "declined"
INVITATION_STATUS_EXPIRED = "expired"
INVITATION_STATUS_REVOKED = "revoked"

MEMBERSHIP_SOURCE_CREATOR = "CREATOR"
MEMBERSHIP_SOURCE_INVITATION = "INVITATION"
MEMBERSHIP_SOURCE_ADMIN = "ADMIN"


class Workspace(StandardModelMixin, Base):
    __tablename__ = "workspaces"

    __table_args__ = (
        CheckConstraint("workspace_type IN ('company', 'agency')", name="workspace_type"),
        Index(
            "ix_workspaces_created_by_user_id",
            "created_by_user_id",
        ),
        Index("ix_workspaces_status", "status"),
        Index("ix_workspaces_is_active", "is_active"),
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    workspace_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="company", server_default="company",
    )
    slug: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=WORKSPACE_STATUS_PROVISIONING,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    timezone: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="UTC",
    )
    logo_url: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
    )
    primary_color: Mapped[str] = mapped_column(
        String(7), nullable=False, default="#2563EB", server_default="#2563EB",
    )
    accent_color: Mapped[str] = mapped_column(
        String(7), nullable=False, default="#F59E0B", server_default="#F59E0B",
    )

    created_by_user: Mapped[User] = relationship(
        User,
        foreign_keys=[created_by_user_id],
    )
    memberships: Mapped[list["WorkspaceMembership"]] = relationship(
        "WorkspaceMembership",
        back_populates="workspace",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    tenant_database: Mapped["TenantDatabaseRegistry | None"] = relationship(
        "TenantDatabaseRegistry",
        back_populates="workspace",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class WorkspaceMembership(StandardModelMixin, Base):
    __tablename__ = "workspace_memberships"

    __table_args__ = (
        UniqueConstraint(
            "workspace_id",
            "user_id",
            name="uq_workspace_memberships_workspace_user",
        ),
        Index(
            "ix_workspace_memberships_user_status",
            "user_id",
            "status",
        ),
        Index(
            "ix_workspace_memberships_workspace_status",
            "workspace_id",
            "status",
        ),
        Index(
            "ix_workspace_memberships_role_key",
            "role_key",
        ),
    )

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role_key: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default=WORKSPACE_ROLE_MEMBER,
    )

    # Compatibility with existing code that reads/writes .role.
    # Both names use the existing role_key database column.
    role = synonym("role_key")

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=MEMBERSHIP_STATUS_ACTIVE,
    )
    source: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=MEMBERSHIP_SOURCE_CREATOR,
    )
    invited_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    invited_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    activated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    joined_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    suspended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    removed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    workspace: Mapped[Workspace] = relationship(
        "Workspace",
        back_populates="memberships",
    )
    user: Mapped[User] = relationship(
        User,
        foreign_keys=[user_id],
    )
    invited_by_user: Mapped[User | None] = relationship(
        User,
        foreign_keys=[invited_by_user_id],
    )


class WorkspaceInvitation(StandardModelMixin, Base):
    __tablename__ = "workspace_invitations"

    __table_args__ = (
        Index(
            "ix_workspace_invitations_workspace_id",
            "workspace_id",
        ),
        Index(
            "ix_workspace_invitations_email",
            "email",
        ),
        Index(
            "ix_workspace_invitations_token_hash",
            "token_hash",
            unique=True,
        ),
        Index(
            "ix_workspace_invitations_status",
            "status",
        ),
        UniqueConstraint(
            "workspace_id",
            "email",
            "status",
            name="uq_workspace_invitations_workspace_email_status",
        ),
    )

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    employee_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        nullable=True,
    )
    email: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
    )
    invited_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    role_key: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default=WORKSPACE_ROLE_MEMBER,
    )
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        nullable=True,
    )
    team_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        nullable=True,
    )
    manager_membership_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "workspace_memberships.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    invited_by_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=INVITATION_STATUS_PENDING,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    declined_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    workspace: Mapped[Workspace] = relationship(
        "Workspace",
    )
    invited_user: Mapped[User | None] = relationship(
        User,
        foreign_keys=[invited_user_id],
    )
    invited_by_user: Mapped[User] = relationship(
        User,
        foreign_keys=[invited_by_user_id],
    )
    manager_membership: Mapped[WorkspaceMembership | None] = relationship(
        WorkspaceMembership,
        foreign_keys=[manager_membership_id],
    )


class TenantDatabaseRegistry(StandardModelMixin, Base):
    __tablename__ = "tenant_database_registry"

    __table_args__ = (
        UniqueConstraint(
            "workspace_id",
            name="uq_tenant_database_registry_workspace_id",
        ),
        UniqueConstraint(
            "database_name",
            name="uq_tenant_database_registry_database_name",
        ),
        Index(
            "ix_tenant_database_registry_status",
            "status",
        ),
    )

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    database_name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )
    cluster_key: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="primary",
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=TENANT_STATUS_PENDING,
    )
    schema_version: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )
    provision_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    provisioned_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    failed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_error_code: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )
    last_error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    workspace: Mapped[Workspace] = relationship(
        "Workspace",
        back_populates="tenant_database",
    )


__all__ = [
    "Workspace",
    "WorkspaceMembership",
    "WorkspaceInvitation",
    "TenantDatabaseRegistry",
    "WORKSPACE_STATUS_PROVISIONING",
    "WORKSPACE_STATUS_READY",
    "WORKSPACE_STATUS_FAILED",
    "WORKSPACE_STATUS_SUSPENDED",
    "WORKSPACE_STATUS_ARCHIVED",
    "MEMBERSHIP_STATUS_ACTIVE",
    "MEMBERSHIP_STATUS_INVITED",
    "MEMBERSHIP_STATUS_SUSPENDED",
    "MEMBERSHIP_STATUS_REMOVED",
    "MEMBERSHIP_SOURCE_CREATOR",
    "MEMBERSHIP_SOURCE_INVITATION",
    "MEMBERSHIP_SOURCE_ADMIN",
    "WORKSPACE_ROLE_OWNER",
    "WORKSPACE_ROLE_ADMIN",
    "WORKSPACE_ROLE_MEMBER",
    "INVITATION_STATUS_PENDING",
    "INVITATION_STATUS_ACCEPTED",
    "INVITATION_STATUS_DECLINED",
    "INVITATION_STATUS_EXPIRED",
    "INVITATION_STATUS_REVOKED",
    "TENANT_STATUS_PENDING",
    "TENANT_STATUS_PROVISIONING",
    "TENANT_STATUS_READY",
    "TENANT_STATUS_FAILED",
    "TENANT_STATUS_SUSPENDED",
    "TENANT_STATUS_DECOMMISSIONED",
]