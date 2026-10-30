from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from app.core.exceptions import ValidationError
from app.modules.workspace_permissions.permissions import (
    WorkspacePermission,
)
from app.modules.workspace_search.access import (
    resolve_search_access,
)


@dataclass(
    frozen=True,
    slots=True,
)
class MonitoringAdminAccess:
    workspace_id: uuid.UUID

    actor_user_id: uuid.UUID

    permissions: frozenset[str]

    can_view: bool

    can_manage: bool

    can_live_view: bool

    can_live_screen: bool

    can_manage_settings: bool


async def resolve_monitoring_admin_access(
    *,
    workspace_id: uuid.UUID,
    context: Any,
) -> MonitoringAdminAccess:
    base = await resolve_search_access(
        workspace_id=workspace_id,
        context=context,
    )

    permissions = frozenset(
        base.permissions
    )

    can_view = (
        WorkspacePermission
        .MONITORING_VIEW
        .value
        in permissions
        or WorkspacePermission
        .MONITORING_SELF_READ
        .value
        in permissions
        or WorkspacePermission
        .MONITORING_TEAM_READ
        .value
        in permissions
        or WorkspacePermission
        .MONITORING_ALL_READ
        .value
        in permissions
    )

    can_manage = (
        WorkspacePermission
        .MONITORING_MANAGE
        .value
        in permissions
    )

    can_live_view = (
        WorkspacePermission
        .MONITORING_LIVE_VIEW
        .value
        in permissions
    )

    can_live_screen = (
        WorkspacePermission
        .MONITORING_LIVE_SCREEN
        .value
        in permissions
    )

    can_manage_settings = (
        WorkspacePermission
        .MONITORING_SETTINGS_MANAGE
        .value
        in permissions
    )

    return MonitoringAdminAccess(
        workspace_id=workspace_id,
        actor_user_id=base.actor_user_id,
        permissions=permissions,
        can_view=can_view,
        can_manage=can_manage,
        can_live_view=can_live_view,
        can_live_screen=can_live_screen,
        can_manage_settings=(
            can_manage_settings
        ),
    )


def require_monitoring_settings_manager(
    access: MonitoringAdminAccess,
) -> None:
    if not access.can_manage_settings:
        raise ValidationError(
            "Monitoring settings management "
            "permission required."
        )


def require_monitoring_view(
    access: MonitoringAdminAccess,
) -> None:
    if not (
        access.can_view
        or access.can_manage
        or access.can_manage_settings
    ):
        raise ValidationError(
            "Monitoring access required."
        )


__all__ = [
    "MonitoringAdminAccess",
    "resolve_monitoring_admin_access",
    "require_monitoring_settings_manager",
    "require_monitoring_view",
]