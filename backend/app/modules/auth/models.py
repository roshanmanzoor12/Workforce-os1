from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.db.base import (
    Base,
    ModelSerializerMixin,
    StandardModelMixin,
)


if TYPE_CHECKING:
    pass


# =========================================================
# USER
# =========================================================


class User(
    StandardModelMixin,
    ModelSerializerMixin,
    Base,
):
    """
    Global WorkforceOS user account.

    IMPORTANT:
    This model belongs to the CONTROL DATABASE.

        workforce_control.users

    It is NOT workspace/tenant specific.

    A single global user can later have memberships in multiple
    WorkforceOS companies/workspaces.

    Example:

        User
            ├── Owner      -> Company A
            ├── Employee   -> Company B
            └── Consultant -> Company C

    Workspace access will be handled later through memberships.
    """

    __tablename__ = "users"

    # -----------------------------------------------------
    # GLOBAL IDENTITY
    # -----------------------------------------------------

    email: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
        unique=True,
        index=True,
    )

    username: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
    )

    # -----------------------------------------------------
    # PROFILE
    # -----------------------------------------------------

    first_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    last_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    avatar_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    avatar_source: Mapped[str] = mapped_column(
        String(16), nullable=False, default="auto", server_default="auto",
    )

    # -----------------------------------------------------
    # LOCAL AUTHENTICATION
    # -----------------------------------------------------

    password_hash: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    """
    password_hash can be NULL because a user may initially register
    through Google or GitHub without a local password.
    """

    # -----------------------------------------------------
    # EMAIL VERIFICATION
    # -----------------------------------------------------

    is_email_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        index=True,
    )

    email_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # -----------------------------------------------------
    # ACCOUNT STATUS
    # -----------------------------------------------------

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        index=True,
    )

    is_locked: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    locked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    locked_reason: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # -----------------------------------------------------
    # SECURITY / LOGIN STATE
    # -----------------------------------------------------

    failed_login_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    password_changed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # -----------------------------------------------------
    # RELATIONSHIPS
    # -----------------------------------------------------

    auth_identities: Mapped[list["AuthIdentity"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    refresh_sessions: Mapped[list["RefreshSession"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    email_verification_challenges: Mapped[
        list["EmailVerificationChallenge"]
    ] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    password_reset_challenges: Mapped[
        list["PasswordResetChallenge"]
    ] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    # -----------------------------------------------------
    # TABLE OPTIONS
    # -----------------------------------------------------

    __table_args__ = (
        Index(
            "ix_users_active_verified",
            "is_active",
            "is_email_verified",
        ),
    )


# =========================================================
# AUTH IDENTITY
# =========================================================


class AuthIdentity(
    StandardModelMixin,
    ModelSerializerMixin,
    Base,
):
    """
    External authentication identity linked to a WorkforceOS user.

    Supported providers initially:

        google
        github

    Local email/password authentication remains directly associated
    with User.password_hash.

    Example:

        WorkforceOS User
            ├── Google identity
            └── GitHub identity

    provider_subject is the unique user identifier returned by
    the external provider.

    Examples:

        Google -> "sub"
        GitHub -> GitHub user ID
    """

    __tablename__ = "auth_identities"

    # -----------------------------------------------------
    # USER
    # -----------------------------------------------------

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # -----------------------------------------------------
    # PROVIDER
    # -----------------------------------------------------

    provider: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
    )

    provider_subject: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # -----------------------------------------------------
    # PROVIDER PROFILE
    # -----------------------------------------------------

    provider_email: Mapped[str | None] = mapped_column(
        String(320),
        nullable=True,
        index=True,
    )

    provider_username: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    provider_avatar_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    provider_email_verified: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    # -----------------------------------------------------
    # LAST AUTHENTICATION
    # -----------------------------------------------------

    last_authenticated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # -----------------------------------------------------
    # RELATIONSHIP
    # -----------------------------------------------------

    user: Mapped["User"] = relationship(
        back_populates="auth_identities",
    )

    # -----------------------------------------------------
    # CONSTRAINTS
    # -----------------------------------------------------

    __table_args__ = (
        UniqueConstraint(
            "provider",
            "provider_subject",
            name="uq_auth_identities_provider_subject",
        ),
        UniqueConstraint(
            "user_id",
            "provider",
            name="uq_auth_identities_user_provider",
        ),
    )


# =========================================================
# REFRESH SESSION
# =========================================================


class RefreshSession(
    StandardModelMixin,
    ModelSerializerMixin,
    Base,
):
    """
    Server-side refresh-token session.

    Access tokens are short lived.

    Refresh tokens correspond to server-side session records so
    WorkforceOS can:

    - revoke one device/session
    - logout one session
    - logout all sessions
    - rotate refresh tokens
    - detect token reuse
    - invalidate sessions after password reset
    """

    __tablename__ = "refresh_sessions"

    # -----------------------------------------------------
    # USER
    # -----------------------------------------------------

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # -----------------------------------------------------
    # JWT / TOKEN IDENTIFIERS
    # -----------------------------------------------------

    jti: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
    )

    token_hash: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        unique=True,
        index=True,
    )

    # -----------------------------------------------------
    # SESSION INFORMATION
    # -----------------------------------------------------

    device_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    user_agent: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    ip_address: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    # -----------------------------------------------------
    # EXPIRATION
    # -----------------------------------------------------

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # -----------------------------------------------------
    # REVOCATION
    # -----------------------------------------------------

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    revoke_reason: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # -----------------------------------------------------
    # REFRESH ROTATION
    # -----------------------------------------------------

    rotated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    replaced_by_session_id: Mapped[uuid.UUID | None] = mapped_column(
        nullable=True,
        index=True,
    )

    # -----------------------------------------------------
    # RELATIONSHIP
    # -----------------------------------------------------

    user: Mapped["User"] = relationship(
        back_populates="refresh_sessions",
    )

    # -----------------------------------------------------
    # HELPERS
    # -----------------------------------------------------

    @property
    def is_revoked(self) -> bool:
        return self.revoked_at is not None


# =========================================================
# EMAIL VERIFICATION CHALLENGE
# =========================================================


class EmailVerificationChallenge(
    StandardModelMixin,
    ModelSerializerMixin,
    Base,
):
    """
    Email verification OTP challenge.

    The actual OTP is NEVER stored.

    Database stores only:

        otp_hash

    Flow:

        signup
           ↓
        OTP generated
           ↓
        HMAC hash stored
           ↓
        OTP emailed
           ↓
        user submits OTP
           ↓
        submitted OTP hashed
           ↓
        constant-time comparison
    """

    __tablename__ = "email_verification_challenges"

    # -----------------------------------------------------
    # USER
    # -----------------------------------------------------

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # -----------------------------------------------------
    # OTP
    # -----------------------------------------------------

    otp_hash: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    # -----------------------------------------------------
    # ATTEMPTS
    # -----------------------------------------------------

    attempt_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    max_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # -----------------------------------------------------
    # CHALLENGE STATE
    # -----------------------------------------------------

    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    consumed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    invalidated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # -----------------------------------------------------
    # DELIVERY INFORMATION
    # -----------------------------------------------------

    sent_to_email: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
    )

    # -----------------------------------------------------
    # RELATIONSHIP
    # -----------------------------------------------------

    user: Mapped["User"] = relationship(
        back_populates="email_verification_challenges",
    )

    # -----------------------------------------------------
    # INDEXES
    # -----------------------------------------------------

    __table_args__ = (
        Index(
            "ix_email_verification_user_expires",
            "user_id",
            "expires_at",
        ),
    )


# =========================================================
# PASSWORD RESET CHALLENGE
# =========================================================


class PasswordResetChallenge(
    StandardModelMixin,
    ModelSerializerMixin,
    Base,
):
    """
    Password-reset OTP challenge.

    Flow:

        forgot password
            ↓
        generate OTP
            ↓
        store OTP HMAC
            ↓
        send email
            ↓
        verify OTP
            ↓
        mark challenge verified
            ↓
        issue temporary reset authorization
            ↓
        new password
            ↓
        consume challenge
            ↓
        revoke old refresh sessions
    """

    __tablename__ = "password_reset_challenges"

    # -----------------------------------------------------
    # USER
    # -----------------------------------------------------

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # -----------------------------------------------------
    # OTP
    # -----------------------------------------------------

    otp_hash: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    # -----------------------------------------------------
    # ATTEMPTS
    # -----------------------------------------------------

    attempt_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    max_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # -----------------------------------------------------
    # VERIFICATION STATE
    # -----------------------------------------------------

    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    consumed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    invalidated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # -----------------------------------------------------
    # RESET AUTHORIZATION
    # -----------------------------------------------------

    reset_token_hash: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        unique=True,
        index=True,
    )

    reset_token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # -----------------------------------------------------
    # REQUEST INFORMATION
    # -----------------------------------------------------

    requested_ip_address: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    requested_user_agent: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # -----------------------------------------------------
    # RELATIONSHIP
    # -----------------------------------------------------

    user: Mapped["User"] = relationship(
        back_populates="password_reset_challenges",
    )

    # -----------------------------------------------------
    # INDEXES
    # -----------------------------------------------------

    __table_args__ = (
        Index(
            "ix_password_reset_user_expires",
            "user_id",
            "expires_at",
        ),
    )


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "User",
    "AuthIdentity",
    "RefreshSession",
    "EmailVerificationChallenge",
    "PasswordResetChallenge",
]