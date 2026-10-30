from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Index,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.db.tenant_base import (
    TenantBase,
    TenantStandardModelMixin,
)


# =========================================================
# TENANT METADATA
# =========================================================


class TenantMetadata(
    TenantStandardModelMixin,
    TenantBase,
):
    """
    Operational identity record stored inside each tenant database.

    Every physical tenant database belongs to exactly one global
    WorkforceOS workspace.

    Important architecture rule:

    workspace_id refers to the global workspace stored in the
    workforce_control database, but it intentionally has NO SQL
    ForeignKey constraint.

    PostgreSQL foreign keys cannot safely span independent tenant
    databases and the control database.

    The trusted backend is responsible for ensuring this workspace_id
    matches the TenantDatabaseRegistry record used to provision and
    route the tenant database.
    """

    __tablename__ = "tenant_metadata"

    __table_args__ = (
        UniqueConstraint(
            "workspace_id",
            name="uq_tenant_metadata_workspace_id",
        ),
        Index(
            "ix_tenant_metadata_is_active",
            "is_active",
        ),
    )

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        nullable=False,
    )

    schema_version: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="0001",
    )

    initialized_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(
            timezone.utc
        ),
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "TenantMetadata",
]