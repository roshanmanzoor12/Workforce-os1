"""phase 11.7 workspace membership compatibility marker

Revision ID: d9e0f1a2b3c4
Revises: c8d9e0f1a2b3
Create Date: 2026-09-11

The workspace_memberships table already exists from the
workspace control-plane migration.

Phase 11.7 reuses that existing model and schema rather than
creating a duplicate membership table.
"""

from typing import (
    Sequence,
    Union,
)


revision: str = "d9e0f1a2b3c4"

down_revision: Union[
    str,
    None,
] = "c8d9e0f1a2b3"

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


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass