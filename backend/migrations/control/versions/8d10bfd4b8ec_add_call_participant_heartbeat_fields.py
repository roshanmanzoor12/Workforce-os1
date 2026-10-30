"""add call participant heartbeat fields

Revision ID: 8d10bfd4b8ec
Revises: ae9bf574e205
Create Date: 2026-10-10 03:00:33.063879

"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



# =========================================================
# REVISION IDENTIFIERS
# =========================================================

revision: str = '8d10bfd4b8ec'

down_revision: Union[str, Sequence[str], None] = 'phase39_chat_features_01'

branch_labels: Union[str, Sequence[str], None] = None

depends_on: Union[str, Sequence[str], None] = None


# =========================================================
# UPGRADE
# =========================================================

def upgrade() -> None:
    """
    Apply this control-database migration.

    IMPORTANT:
    These migrations are intended for the WorkforceOS control
    database only.

    They must not be used for tenant databases.
    """

    pass


# =========================================================
# DOWNGRADE
# =========================================================

def downgrade() -> None:
    """
    Reverse this control-database migration.

    Use downgrade carefully in production because destructive
    schema operations may remove data.
    """

    pass
