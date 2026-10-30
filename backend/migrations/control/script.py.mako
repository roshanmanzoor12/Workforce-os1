"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}


# =========================================================
# REVISION IDENTIFIERS
# =========================================================

revision: str = ${repr(up_revision)}

down_revision: Union[str, Sequence[str], None] = ${repr(down_revision)}

branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}

depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


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

    ${upgrades if upgrades else "pass"}


# =========================================================
# DOWNGRADE
# =========================================================

def downgrade() -> None:
    """
    Reverse this control-database migration.

    Use downgrade carefully in production because destructive
    schema operations may remove data.
    """

    ${downgrades if downgrades else "pass"}