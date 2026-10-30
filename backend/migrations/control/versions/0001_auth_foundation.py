"""Create WorkforceOS authentication foundation.

Revision ID: 0001_auth_foundation
Revises:
Create Date: 2026-08-20

This is the first Alembic-managed WorkforceOS control-database
migration.

It creates the global authentication foundation:

- users
- auth_identities
- refresh_sessions
- email_verification_challenges
- password_reset_challenges

Workspace, membership, subscription, billing, and tenant-registry
tables will be introduced by their own modules/migrations later.

This migration belongs only to:

    workforce_control

It must never be executed against a tenant database.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# =========================================================
# REVISION IDENTIFIERS
# =========================================================

revision: str = "0001_auth_foundation"

down_revision: Union[
    str,
    Sequence[str],
    None,
] = None

branch_labels: Union[
    str,
    Sequence[str],
    None,
] = None

depends_on: Union[
    str,
    Sequence[str],
    None,
] = None


# =========================================================
# UPGRADE
# =========================================================


def upgrade() -> None:
    """
    Create the global authentication schema.
    """

    # =====================================================
    # USERS
    # =====================================================

    op.create_table(
        "users",

        sa.Column(
            "email",
            sa.String(length=320),
            nullable=False,
        ),

        sa.Column(
            "username",
            sa.String(length=64),
            nullable=False,
        ),

        sa.Column(
            "first_name",
            sa.String(length=100),
            nullable=True,
        ),

        sa.Column(
            "last_name",
            sa.String(length=100),
            nullable=True,
        ),

        sa.Column(
            "avatar_url",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "password_hash",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "is_email_verified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),

        sa.Column(
            "email_verified_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),

        sa.Column(
            "is_locked",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),

        sa.Column(
            "locked_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        sa.Column(
            "locked_reason",
            sa.String(length=500),
            nullable=True,
        ),

        sa.Column(
            "failed_login_attempts",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),

        sa.Column(
            "last_login_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        sa.Column(
            "password_changed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        # -------------------------------------------------
        # STANDARD MODEL FIELDS
        # -------------------------------------------------

        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),

        sa.PrimaryKeyConstraint(
            "id",
            name=op.f(
                "pk_users"
            ),
        ),
    )

    # -----------------------------------------------------
    # USERS INDEXES
    # -----------------------------------------------------

    op.create_index(
        op.f(
            "ix_users_email"
        ),
        "users",
        [
            "email",
        ],
        unique=True,
    )

    op.create_index(
        op.f(
            "ix_users_username"
        ),
        "users",
        [
            "username",
        ],
        unique=True,
    )

    op.create_index(
        op.f(
            "ix_users_is_email_verified"
        ),
        "users",
        [
            "is_email_verified",
        ],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_users_is_active"
        ),
        "users",
        [
            "is_active",
        ],
        unique=False,
    )


    # =====================================================
    # AUTH IDENTITIES
    # =====================================================

    op.create_table(
        "auth_identities",

        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),

        sa.Column(
            "provider",
            sa.String(length=32),
            nullable=False,
        ),

        sa.Column(
            "provider_subject",
            sa.String(length=255),
            nullable=False,
        ),

        sa.Column(
            "provider_email",
            sa.String(length=320),
            nullable=True,
        ),

        sa.Column(
            "provider_username",
            sa.String(length=255),
            nullable=True,
        ),

        sa.Column(
            "provider_avatar_url",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "provider_email_verified",
            sa.Boolean(),
            nullable=True,
        ),

        sa.Column(
            "last_authenticated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),

        sa.ForeignKeyConstraint(
            [
                "user_id",
            ],
            [
                "users.id",
            ],
            name=op.f(
                "fk_auth_identities_user_id_users"
            ),
            ondelete="CASCADE",
        ),

        sa.PrimaryKeyConstraint(
            "id",
            name=op.f(
                "pk_auth_identities"
            ),
        ),

        sa.UniqueConstraint(
            "provider",
            "provider_subject",
            name="uq_auth_identity_provider_subject",
        ),

        sa.UniqueConstraint(
            "user_id",
            "provider",
            name="uq_auth_identity_user_provider",
        ),
    )

    op.create_index(
        op.f(
            "ix_auth_identities_user_id"
        ),
        "auth_identities",
        [
            "user_id",
        ],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_auth_identities_provider"
        ),
        "auth_identities",
        [
            "provider",
        ],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_auth_identities_provider_subject"
        ),
        "auth_identities",
        [
            "provider_subject",
        ],
        unique=False,
    )


    # =====================================================
    # REFRESH SESSIONS
    # =====================================================

    op.create_table(
        "refresh_sessions",

        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),

        sa.Column(
            "jti",
            sa.String(length=64),
            nullable=False,
        ),

        sa.Column(
            "token_hash",
            sa.String(length=128),
            nullable=False,
        ),

        sa.Column(
            "device_name",
            sa.String(length=255),
            nullable=True,
        ),

        sa.Column(
            "user_agent",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "ip_address",
            sa.String(length=64),
            nullable=True,
        ),

        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),

        sa.Column(
            "last_used_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        sa.Column(
            "revoked_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        sa.Column(
            "revoke_reason",
            sa.String(length=255),
            nullable=True,
        ),

        sa.Column(
            "rotated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        sa.Column(
            "replaced_by_session_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),

        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),

        sa.ForeignKeyConstraint(
            [
                "user_id",
            ],
            [
                "users.id",
            ],
            name=op.f(
                "fk_refresh_sessions_user_id_users"
            ),
            ondelete="CASCADE",
        ),

        sa.PrimaryKeyConstraint(
            "id",
            name=op.f(
                "pk_refresh_sessions"
            ),
        ),
    )

    op.create_index(
        op.f(
            "ix_refresh_sessions_user_id"
        ),
        "refresh_sessions",
        [
            "user_id",
        ],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_refresh_sessions_jti"
        ),
        "refresh_sessions",
        [
            "jti",
        ],
        unique=True,
    )

    op.create_index(
        op.f(
            "ix_refresh_sessions_token_hash"
        ),
        "refresh_sessions",
        [
            "token_hash",
        ],
        unique=True,
    )

    op.create_index(
        op.f(
            "ix_refresh_sessions_expires_at"
        ),
        "refresh_sessions",
        [
            "expires_at",
        ],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_refresh_sessions_revoked_at"
        ),
        "refresh_sessions",
        [
            "revoked_at",
        ],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_refresh_sessions_replaced_by_session_id"
        ),
        "refresh_sessions",
        [
            "replaced_by_session_id",
        ],
        unique=False,
    )


    # =====================================================
    # EMAIL VERIFICATION CHALLENGES
    # =====================================================

    op.create_table(
        "email_verification_challenges",

        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),

        sa.Column(
            "otp_hash",
            sa.String(length=128),
            nullable=False,
        ),

        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),

        sa.Column(
            "attempt_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),

        sa.Column(
            "max_attempts",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "verified_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        sa.Column(
            "consumed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        sa.Column(
            "invalidated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        sa.Column(
            "sent_to_email",
            sa.String(length=320),
            nullable=False,
        ),

        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),

        sa.ForeignKeyConstraint(
            [
                "user_id",
            ],
            [
                "users.id",
            ],
            name=op.f(
                "fk_email_verification_challenges_user_id_users"
            ),
            ondelete="CASCADE",
        ),

        sa.PrimaryKeyConstraint(
            "id",
            name=op.f(
                "pk_email_verification_challenges"
            ),
        ),
    )

    op.create_index(
        op.f(
            "ix_email_verification_challenges_user_id"
        ),
        "email_verification_challenges",
        [
            "user_id",
        ],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_email_verification_challenges_expires_at"
        ),
        "email_verification_challenges",
        [
            "expires_at",
        ],
        unique=False,
    )


    # =====================================================
    # PASSWORD RESET CHALLENGES
    # =====================================================

    op.create_table(
        "password_reset_challenges",

        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),

        sa.Column(
            "otp_hash",
            sa.String(length=128),
            nullable=False,
        ),

        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),

        sa.Column(
            "attempt_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),

        sa.Column(
            "max_attempts",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "verified_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        sa.Column(
            "consumed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        sa.Column(
            "invalidated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        sa.Column(
            "reset_token_hash",
            sa.String(length=128),
            nullable=True,
        ),

        sa.Column(
            "reset_token_expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        sa.Column(
            "requested_ip_address",
            sa.String(length=64),
            nullable=True,
        ),

        sa.Column(
            "requested_user_agent",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),

        sa.ForeignKeyConstraint(
            [
                "user_id",
            ],
            [
                "users.id",
            ],
            name=op.f(
                "fk_password_reset_challenges_user_id_users"
            ),
            ondelete="CASCADE",
        ),

        sa.PrimaryKeyConstraint(
            "id",
            name=op.f(
                "pk_password_reset_challenges"
            ),
        ),
    )

    op.create_index(
        op.f(
            "ix_password_reset_challenges_user_id"
        ),
        "password_reset_challenges",
        [
            "user_id",
        ],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_password_reset_challenges_expires_at"
        ),
        "password_reset_challenges",
        [
            "expires_at",
        ],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_password_reset_challenges_reset_token_hash"
        ),
        "password_reset_challenges",
        [
            "reset_token_hash",
        ],
        unique=True,
    )


# =========================================================
# DOWNGRADE
# =========================================================


def downgrade() -> None:
    """
    Remove authentication foundation.

    Child tables must be dropped before users.
    """

    # =====================================================
    # PASSWORD RESET
    # =====================================================

    op.drop_index(
        op.f(
            "ix_password_reset_challenges_reset_token_hash"
        ),
        table_name="password_reset_challenges",
    )

    op.drop_index(
        op.f(
            "ix_password_reset_challenges_expires_at"
        ),
        table_name="password_reset_challenges",
    )

    op.drop_index(
        op.f(
            "ix_password_reset_challenges_user_id"
        ),
        table_name="password_reset_challenges",
    )

    op.drop_table(
        "password_reset_challenges"
    )


    # =====================================================
    # EMAIL VERIFICATION
    # =====================================================

    op.drop_index(
        op.f(
            "ix_email_verification_challenges_expires_at"
        ),
        table_name="email_verification_challenges",
    )

    op.drop_index(
        op.f(
            "ix_email_verification_challenges_user_id"
        ),
        table_name="email_verification_challenges",
    )

    op.drop_table(
        "email_verification_challenges"
    )


    # =====================================================
    # REFRESH SESSIONS
    # =====================================================

    op.drop_index(
        op.f(
            "ix_refresh_sessions_replaced_by_session_id"
        ),
        table_name="refresh_sessions",
    )

    op.drop_index(
        op.f(
            "ix_refresh_sessions_revoked_at"
        ),
        table_name="refresh_sessions",
    )

    op.drop_index(
        op.f(
            "ix_refresh_sessions_expires_at"
        ),
        table_name="refresh_sessions",
    )

    op.drop_index(
        op.f(
            "ix_refresh_sessions_token_hash"
        ),
        table_name="refresh_sessions",
    )

    op.drop_index(
        op.f(
            "ix_refresh_sessions_jti"
        ),
        table_name="refresh_sessions",
    )

    op.drop_index(
        op.f(
            "ix_refresh_sessions_user_id"
        ),
        table_name="refresh_sessions",
    )

    op.drop_table(
        "refresh_sessions"
    )


    # =====================================================
    # AUTH IDENTITIES
    # =====================================================

    op.drop_index(
        op.f(
            "ix_auth_identities_provider_subject"
        ),
        table_name="auth_identities",
    )

    op.drop_index(
        op.f(
            "ix_auth_identities_provider"
        ),
        table_name="auth_identities",
    )

    op.drop_index(
        op.f(
            "ix_auth_identities_user_id"
        ),
        table_name="auth_identities",
    )

    op.drop_table(
        "auth_identities"
    )


    # =====================================================
    # USERS
    # =====================================================

    op.drop_index(
        op.f(
            "ix_users_is_active"
        ),
        table_name="users",
    )

    op.drop_index(
        op.f(
            "ix_users_is_email_verified"
        ),
        table_name="users",
    )

    op.drop_index(
        op.f(
            "ix_users_username"
        ),
        table_name="users",
    )

    op.drop_index(
        op.f(
            "ix_users_email"
        ),
        table_name="users",
    )

    op.drop_table(
        "users"
    )