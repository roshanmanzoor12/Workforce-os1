from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
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
# DEVICE ROUTE STATUSES
# =========================================================

DEVICE_ROUTE_STATUS_ACTIVE = "active"
DEVICE_ROUTE_STATUS_REVOKED = "revoked"

DEVICE_ROUTE_STATUSES = (
    DEVICE_ROUTE_STATUS_ACTIVE,
    DEVICE_ROUTE_STATUS_REVOKED,
)


# =========================================================
# DEVICE ROUTE
# =========================================================


class DeviceRoute(
    StandardModelMixin,
    Base,
):
    """
    Control-plane routing identity for one registered endpoint.

    Purpose:

        public agent request
            -> device_uuid
            -> workforce_control
            -> trusted workspace_id
            -> trusted TenantDatabaseRegistry
            -> correct tenant database

    This prevents the backend from scanning every tenant database
    to locate a device.

    Security boundaries:

    - the agent never supplies database_name or cluster_key
    - workspace_id is resolved from this trusted control row
    - tenant_device_id is an informational cross-database UUID only;
      it intentionally has no foreign key because Device lives in
      another physical PostgreSQL database
    """

    __tablename__ = "device_routes"

    __table_args__ = (
        # -------------------------------------------------
        # GLOBAL DEVICE ROUTING IDENTITY
        # -------------------------------------------------

        UniqueConstraint(
            "device_uuid",
            name="uq_device_routes_device_uuid",
        ),

        # -------------------------------------------------
        # TENANT DEVICE IDENTITY
        # -------------------------------------------------

        UniqueConstraint(
            "workspace_id",
            "tenant_device_id",
            name=(
                "uq_device_routes_"
                "workspace_id_tenant_device_id"
            ),
        ),

        # -------------------------------------------------
        # STATUS
        # -------------------------------------------------

        CheckConstraint(
            (
                "status IN "
                "('active', 'revoked')"
            ),
            name="ck_device_routes_status",
        ),

        # -------------------------------------------------
        # QUERY INDEXES
        # -------------------------------------------------

        Index(
            "ix_device_routes_workspace_id",
            "workspace_id",
        ),

        Index(
            "ix_device_routes_status",
            "status",
        ),

        Index(
            "ix_device_routes_is_active",
            "is_active",
        ),
    )

    # =====================================================
    # WORKSPACE BINDING
    # =====================================================

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "workspaces.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    # =====================================================
    # PUBLIC DEVICE ROUTING IDENTITY
    # =====================================================

    device_uuid: Mapped[uuid.UUID] = mapped_column(
        nullable=False,
    )

    # =====================================================
    # TENANT-LOCAL DEVICE IDENTITY
    # =====================================================

    tenant_device_id: Mapped[uuid.UUID] = mapped_column(
        nullable=False,
    )

    # =====================================================
    # LIFECYCLE
    # =====================================================

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=DEVICE_ROUTE_STATUS_ACTIVE,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    registered_at: Mapped[datetime | None] = mapped_column(
        DateTime(
            timezone=True
        ),
        nullable=True,
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(
            timezone=True
        ),
        nullable=True,
    )


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "DEVICE_ROUTE_STATUS_ACTIVE",
    "DEVICE_ROUTE_STATUS_REVOKED",
    "DEVICE_ROUTE_STATUSES",
    "DeviceRoute",
]