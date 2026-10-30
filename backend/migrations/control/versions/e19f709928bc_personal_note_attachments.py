"""personal note attachments"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'e19f709928bc'
down_revision = 'pn20261013_01'
branch_labels = None
depends_on = None


def upgrade():
    # PostgreSQL must commit a new enum value before it is used.
    with op.get_context().autocommit_block():
        op.execute(
            "ALTER TYPE attachment_scope "
            "ADD VALUE IF NOT EXISTS 'NOTE'"
        )

    op.add_column(
        "attachments",
        sa.Column(
            "personal_note_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )

    op.create_foreign_key(
        "fk_attachments_personal_note_id",
        "attachments",
        "personal_notes",
        ["personal_note_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    op.create_index(
        "ix_attachments_personal_note_id",
        "attachments",
        ["personal_note_id"],
    )


def downgrade():
    connection = op.get_bind()

    count = connection.execute(
        sa.text(
            "SELECT count(*) FROM attachments "
            "WHERE scope::text = 'NOTE'"
        )
    ).scalar_one()

    if count:
        raise RuntimeError(
            "NOTE attachment records exist. "
            "Resolve them before downgrading."
        )

    op.drop_index(
        "ix_attachments_personal_note_id",
        table_name="attachments",
    )

    op.drop_constraint(
        "fk_attachments_personal_note_id",
        "attachments",
        type_="foreignkey",
    )

    op.drop_column(
        "attachments",
        "personal_note_id",
    )

    # Retain the unused enum label. Removing PostgreSQL enum
    # values requires recreating the type and is unnecessary.
