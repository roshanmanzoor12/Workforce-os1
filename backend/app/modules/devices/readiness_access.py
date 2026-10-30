from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from app.core.exceptions import (
    ValidationError,
)
from app.modules.desktop_agent.access import (
    resolve_desktop_agent_access,
)
from app.modules.workspace_permissions.permissions import (
    WorkspacePermission,
)


# =========================================================
# ACCESS RESULT
# =========================================================


@dataclass(
    frozen=True,
    slots=True,
)
class DeviceReadinessAccess:
    workspace_id: uuid.UUID

    actor_user_id: uuid.UUID

    actor_employee_id: (
        uuid.UUID
        | None
    )

    visible_employee_ids: (
        frozenset[
            uuid.UUID
        ]
        | None
    )

    permissions: frozenset[
        str
    ]

    can_manage: bool


# =========================================================
# PERMISSION SET
# =========================================================


DEVICE_READ_PERMISSIONS = frozenset(
    {
        WorkspacePermission
        .DEVICES_SELF_READ
        .value,

        WorkspacePermission
        .DEVICES_TEAM_READ
        .value,

        WorkspacePermission
        .DEVICES_ALL_READ
        .value,

        WorkspacePermission
        .DEVICES_MANAGE
        .value,
    }
)


# =========================================================
# RESOLUTION
# =========================================================


async def resolve_device_readiness_access(
    *,
    workspace_id: uuid.UUID,
    context: Any,
) -> DeviceReadinessAccess:
    base = await (
        resolve_desktop_agent_access(
            workspace_id=workspace_id,
            context=context,
        )
    )

    if not (
        DEVICE_READ_PERMISSIONS
        & base.permissions
    ):
        raise ValidationError(
            "Device read permission "
            "is required."
        )

    return DeviceReadinessAccess(
        workspace_id=workspace_id,

        actor_user_id=(
            base.actor_user_id
        ),

        actor_employee_id=(
            base.actor_employee_id
        ),

        visible_employee_ids=(
            base.visible_employee_ids
        ),

        permissions=(
            base.permissions
        ),

        can_manage=(
            base.can_manage
        ),
    )


__all__ = [
    "DEVICE_READ_PERMISSIONS",
    "DeviceReadinessAccess",
    "resolve_device_readiness_access",
]