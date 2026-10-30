from __future__ import annotations

import uuid
from collections.abc import Collection

from fastapi import HTTPException, status

from app.modules.workspaces.models import MEMBERSHIP_STATUS_ACTIVE


SCOPE_MANAGEMENT_PERMISSION = "roles.manage"


def require_scope_manager(
    membership: object,
    *,
    workspace_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    permissions: Collection[str],
) -> None:
    """
    Initial scope administration is restricted to primary owners.

    Additional roles and custom permissions cannot establish ownership.
    The effective permission snapshot is still required.
    """

    allowed = (
        getattr(membership, "workspace_id", None) == workspace_id
        and getattr(membership, "user_id", None) == actor_user_id
        and getattr(membership, "status", None)
        == MEMBERSHIP_STATUS_ACTIVE
        and getattr(membership, "role_key", None) == "owner"
        and SCOPE_MANAGEMENT_PERMISSION in permissions
    )

    if allowed:
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=(
            "A primary workspace owner with roles.manage "
            "is required to manage saved scopes."
        ),
    )


__all__ = [
    "SCOPE_MANAGEMENT_PERMISSION",
    "require_scope_manager",
]