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

from app.db.base import (
    Base,
    StandardModelMixin,
)


# =========================================================
# ACTIVATION STATUSES
# =========================================================

ACTIVATION_STATUS_ACTIVE = "active"
ACTIVATION_STATUS_EXPIRED = "expired"
ACTIVATION_STATUS_REVOKED = "revoked"
ACTIVATION_STATUS_EXHAUSTED = "exhausted"

ACTIVATION_STATUSES = (
    ACTIVATION_STATUS_ACTIVE,
    ACTIVATION_STATUS_EXPIRED,
    ACTIVATION_STATUS_REVOKED,
    ACTIVATION_STATUS_EXHAUSTED,
)


# =========================================================
# DEVICE ACTIVATION CODE
# =========================================================


class DeviceActivationCode(
    StandardModelMixin,
    Base,
):
    """
    Control-plane endpoint enrollment secret.

    This model exists in workforce_control because the backend
    must resolve a trusted workspace before opening any tenant DB.

    Security properties:

    - plaintext activation code is never persisted
    - only code_hash is stored
    - each activation belongs to exactly one workspace
    - usage may be limited
    - codes may expire or be revoked
    """

    __tablename__ = "device_activation_codes"

    __table_args__ = (
        # -------------------------------------------------
        # UNIQUE SECRET LOOKUP
        # -------------------------------------------------

        UniqueConstraint(
            "code_hash",
            name="uq_device_activation_codes_code_hash",
        ),

        # -------------------------------------------------
        # STATUS VALIDATION
        # -------------------------------------------------

        CheckConstraint(
            (
                "status IN "
                "('active', 'expired', "
                "'revoked', 'exhausted')"
            ),
            name="ck_device_activation_codes_status",
        ),

        CheckConstraint(
            (
                "max_uses IS NULL "
                "OR max_uses > 0"
            ),
            name=(
                "ck_device_activation_codes_"
                "max_uses_positive"
            ),
        ),

        CheckConstraint(
            "used_count >= 0",
            name=(
                "ck_device_activation_codes_"
                "used_count_nonnegative"
            ),
        ),

        # -------------------------------------------------
        # QUERY INDEXES
        # -------------------------------------------------

        Index(
            "ix_device_activation_codes_workspace_id",
            "workspace_id",
        ),

        Index(
            "ix_device_activation_codes_status",
            "status",
        ),

        Index(
            "ix_device_activation_codes_expires_at",
            "expires_at",
        ),

        Index(
            "ix_device_activation_codes_is_active",
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

    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    # =====================================================
    # SECRET MATERIAL
    # =====================================================

    code_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    code_prefix: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )

    # =====================================================
    # LIFECYCLE
    # =====================================================

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=ACTIVATION_STATUS_ACTIVE,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
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

    # =====================================================
    # USAGE LIMITS
    # =====================================================

    max_uses: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    used_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # =====================================================
    # ADMIN LABEL
    # =====================================================

    label: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "ACTIVATION_STATUS_ACTIVE",
    "ACTIVATION_STATUS_EXPIRED",
    "ACTIVATION_STATUS_REVOKED",
    "ACTIVATION_STATUS_EXHAUSTED",
    "ACTIVATION_STATUSES",
    "DeviceActivationCode",
]