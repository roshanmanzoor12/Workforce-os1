"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

Tenant migration only.

This migration belongs to WorkforceOS tenant databases:

    tenant_<workspace_uuid_hex>

It must never be executed against:

    workforce_control
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

down_revision: Union[
    str,
    Sequence[str],
    None,
] = ${repr(down_revision)}

branch_labels: Union[
    str,
    Sequence[str],
    None,
] = ${repr(branch_labels)}

depends_on: Union[
    str,
    Sequence[str],
    None,
] = ${repr(depends_on)}


# =========================================================
# UPGRADE
# =========================================================


def upgrade() -> None:
    """
    Apply this migration to exactly one tenant database.

    Important:

    - this migration must use TenantBase metadata
    - it must not create control-plane tables
    - it must not reference workforce_control tables with
      cross-database foreign keys
    """
    ${upgrades if upgrades else "pass"}


# =========================================================
# DOWNGRADE
# =========================================================


def downgrade() -> None:
    """
    Reverse this tenant migration.

    Downgrades may destroy tenant data and should be used
    carefully outside development/test environments.
    """
    ${downgrades if downgrades else "pass"}