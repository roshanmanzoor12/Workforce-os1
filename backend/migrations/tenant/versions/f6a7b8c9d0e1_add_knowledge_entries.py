"""add knowledge entries

Revision ID: f6a7b8c9d0e1
Revises: e4f5a6b7c8d9
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "f6a7b8c9d0e1"
down_revision = "e4f5a6b7c8d9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "knowledge_entries",
        sa.Column(
            "id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),
        sa.Column(
            "owner_employee_id",
            postgresql.UUID(
                as_uuid=True
            ),
            nullable=False,
        ),
        sa.Column(
            "title",
            sa.String(
                length=250
            ),
            nullable=False,
        ),
        sa.Column(
            "content",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "category",
            sa.String(
                length=32
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(
                length=32
            ),
            nullable=False,
        ),
        sa.Column(
            "visibility",
            sa.String(
                length=32
            ),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(
                timezone=True
            ),
            nullable=False,
        ),
        sa.CheckConstraint(
            (
                "status IN "
                "('draft', 'published', 'archived')"
            ),
            name="ck_knowledge_entries_status",
        ),
        sa.CheckConstraint(
            (
                "visibility IN "
                "('private', 'workspace')"
            ),
            name=(
                "ck_knowledge_entries_visibility"
            ),
        ),
        sa.CheckConstraint(
            (
                "category IN "
                "('general', 'process', "
                "'reference', 'learning')"
            ),
            name=(
                "ck_knowledge_entries_category"
            ),
        ),
        sa.ForeignKeyConstraint(
            [
                "owner_employee_id",
            ],
            [
                "employees.id",
            ],
            name=(
                "fk_knowledge_entries_"
                "owner_employee_id_employees"
            ),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name="pk_knowledge_entries",
        ),
    )

    op.create_index(
        "ix_knowledge_entries_owner",
        "knowledge_entries",
        [
            "owner_employee_id",
        ],
        unique=False,
    )

    op.create_index(
        "ix_knowledge_entries_status",
        "knowledge_entries",
        [
            "status",
        ],
        unique=False,
    )

    op.create_index(
        "ix_knowledge_entries_visibility",
        "knowledge_entries",
        [
            "visibility",
        ],
        unique=False,
    )

    op.create_index(
        "ix_knowledge_entries_category",
        "knowledge_entries",
        [
            "category",
        ],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_knowledge_entries_category",
        table_name="knowledge_entries",
    )

    op.drop_index(
        "ix_knowledge_entries_visibility",
        table_name="knowledge_entries",
    )

    op.drop_index(
        "ix_knowledge_entries_status",
        table_name="knowledge_entries",
    )

    op.drop_index(
        "ix_knowledge_entries_owner",
        table_name="knowledge_entries",
    )

    op.drop_table(
        "knowledge_entries"
    )