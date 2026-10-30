"""Persist the user's photo choice and backfill existing Google photos."""
from alembic import op
import sqlalchemy as sa

revision = "av20261016_01"
down_revision = "e19f709928bc"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("avatar_source", sa.String(16),
                                    nullable=False, server_default="auto"))
    # Existing manually supplied URLs remain custom, including users with Google.
    op.execute("""
        UPDATE users AS u SET avatar_source = 'url'
        WHERE NULLIF(BTRIM(u.avatar_url), '') IS NOT NULL
          AND NOT EXISTS (
            SELECT 1 FROM auth_identities AS a WHERE a.user_id = u.id
              AND a.provider = 'google' AND a.provider_avatar_url = u.avatar_url
          )
    """)
    op.execute("""
        UPDATE users AS u SET avatar_url = chosen.provider_avatar_url,
                             avatar_source = 'google'
        FROM (
          SELECT DISTINCT ON (user_id) user_id, provider_avatar_url
          FROM auth_identities
          WHERE provider = 'google'
            AND NULLIF(BTRIM(provider_avatar_url), '') IS NOT NULL
          ORDER BY user_id, created_at DESC, id DESC
        ) AS chosen
        WHERE u.id = chosen.user_id AND u.avatar_source = 'auto'
    """)


def downgrade():
    op.drop_column("users", "avatar_source")
