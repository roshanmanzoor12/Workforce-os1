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
    UniqueConstraint,
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
# DEVICE CREDENTIAL STATUSES
# =========================================================

DEVICE_CREDENTIAL_STATUS_ACTIVE = "active"
DEVICE_CREDENTIAL_STATUS_REVOKED = "revoked"
DEVICE_CREDENTIAL_STATUS_EXPIRED = "expired"

DEVICE_CREDENTIAL_STATUSES = (
    DEVICE_CREDENTIAL_STATUS_ACTIVE,
    DEVICE_CREDENTIAL_STATUS_REVOKED,
    DEVICE_CREDENTIAL_STATUS_EXPIRED,
)


# =========================================================
# DEVICE CREDENTIAL
# =========================================================


class DeviceCredential(
    TenantStandardModelMixin,
    TenantBase,
):
    """
    Tenant-local authentication credential for one registered device.

    Security model:

        activation code
            -> bootstrap enrollment only

        device credential
            -> permanent/rotatable agent authentication

    Important:

    - plaintext device secret is NEVER stored
    - secret_hash stores only the cryptographic digest
    - secret_prefix is safe display/debug metadata
    - credentials can be rotated
    - old credentials can be revoked without deleting Device
    - multiple credential rows allow controlled rotation history
    """

    __tablename__ = "device_credentials"

    __table_args__ = (
        # -------------------------------------------------
        # SECRET UNIQUENESS
        # -------------------------------------------------

        UniqueConstraint(
            "secret_hash",
            name="uq_device_credentials_secret_hash",
        ),

        # -------------------------------------------------
        # VERSION UNIQUENESS PER DEVICE
        # -------------------------------------------------

        UniqueConstraint(
            "device_id",
            "version",
            name="uq_device_credentials_device_id_version",
        ),

        # -------------------------------------------------
        # STATUS VALIDATION
        # -------------------------------------------------

        CheckConstraint(
            (
                "status IN "
                "('active', 'revoked', 'expired')"
            ),
            name="ck_device_credentials_status",
        ),

        CheckConstraint(
            "version > 0",
            name="ck_device_credentials_version_positive",
        ),

        # -------------------------------------------------
        # QUERY INDEXES
        # -------------------------------------------------

        Index(
            "ix_device_credentials_device_id",
            "device_id",
        ),

        Index(
            "ix_device_credentials_status",
            "status",
        ),

        Index(
            "ix_device_credentials_is_active",
            "is_active",
        ),

        Index(
            "ix_device_credentials_expires_at",
            "expires_at",
        ),

        Index(
            "ix_device_credentials_last_used_at",
            "last_used_at",
        ),
    )

    # =====================================================
    # DEVICE BINDING
    # =====================================================

    device_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "devices.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    # =====================================================
    # SECRET MATERIAL
    # =====================================================

    secret_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    secret_prefix: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )

    # =====================================================
    # CREDENTIAL VERSION
    # =====================================================

    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    # =====================================================
    # LIFECYCLE
    # =====================================================

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=DEVICE_CREDENTIAL_STATUS_ACTIVE,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    issued_at: Mapped[datetime | None] = mapped_column(
        DateTime(
            timezone=True
        ),
        nullable=True,
    )

    expires_at: Mapped[datetime | None] = mapped_column(
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

    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(
            timezone=True
        ),
        nullable=True,
    )


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "DEVICE_CREDENTIAL_STATUS_ACTIVE",
    "DEVICE_CREDENTIAL_STATUS_REVOKED",
    "DEVICE_CREDENTIAL_STATUS_EXPIRED",
    "DEVICE_CREDENTIAL_STATUSES",
    "DeviceCredential",
]