"""add realtime call participant heartbeat columns

Revision ID: f8f84f4bd3c9
Revises: 8d10bfd4b8ec
Create Date: 2026-10-10 03:04:24.805224
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "f8f84f4bd3c9"

down_revision: Union[str, Sequence[str], None] = "8d10bfd4b8ec"

branch_labels: Union[str, Sequence[str], None] = None

depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "realtime_call_participants",
        sa.Column(
            "connection_id",
            sa.String(length=255),
            nullable=True,
        ),
    )

    op.add_column(
        "realtime_call_participants",
        sa.Column(
            "last_heartbeat_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_realtime_call_participants_last_heartbeat_at",
        "realtime_call_participants",
        ["last_heartbeat_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_realtime_call_participants_last_heartbeat_at",
        table_name="realtime_call_participants",
    )

    op.drop_column(
        "realtime_call_participants",
        "last_heartbeat_at",
    )

    op.drop_column(
        "realtime_call_participants",
        "connection_id",
    )