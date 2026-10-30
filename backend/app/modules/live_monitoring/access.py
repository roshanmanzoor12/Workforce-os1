from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from app.core.exceptions import (
    ValidationError,
)
from app.modules.desktop_agent.access import (
    DesktopAgentAccess,
    resolve_desktop_agent_access,
)
from app.modules.desktop_agent.models import (
    DesktopAgentDevice,
)
from app.modules.desktop_agent.repository import (
    DesktopAgentRepository,
)
from app.modules.workspace_permissions.permissions import (
    WorkspacePermission,
)


@dataclass(
    frozen=True,
    slots=True,
)
class LiveMonitoringAccess:
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

    can_request_screenshot: bool

    can_request_live_screen: bool

    can_manage_settings: bool


async def resolve_live_monitoring_access(
    *,
    workspace_id: uuid.UUID,
    context: Any,
) -> LiveMonitoringAccess:
    device_access = await (
        resolve_desktop_agent_access(
            workspace_id=workspace_id,
            context=context,
        )
    )

    permissions = (
        device_access.permissions
    )

    return LiveMonitoringAccess(
        workspace_id=workspace_id,

        actor_user_id=(
            device_access
            .actor_user_id
        ),

        actor_employee_id=(
            device_access
            .actor_employee_id
        ),

        visible_employee_ids=(
            device_access
            .visible_employee_ids
        ),

        can_request_screenshot=(
            WorkspacePermission
            .MONITORING_LIVE_VIEW
            .value
            in permissions
        ),

        can_request_live_screen=(
            WorkspacePermission
            .MONITORING_LIVE_SCREEN
            .value
            in permissions
        ),

        can_manage_settings=(
            WorkspacePermission
            .MONITORING_SETTINGS_MANAGE
            .value
            in permissions
        ),
    )


def can_access_employee(
    *,
    access: LiveMonitoringAccess,
    employee_id: uuid.UUID,
) -> bool:
    if access.visible_employee_ids is None:
        return True

    return (
        employee_id
        in access.visible_employee_ids
    )


async def resolve_device_for_request(
    *,
    context: Any,
    access: LiveMonitoringAccess,
    device_id: uuid.UUID,
) -> DesktopAgentDevice:
    repository = (
        DesktopAgentRepository(
            context.tenant_session
        )
    )

    device = await repository.get(
        device_id=device_id
    )

    if device is None:
        raise ValidationError(
            "Desktop agent device not found."
        )

    if device.is_disabled:
        raise ValidationError(
            "Desktop agent device is disabled."
        )

    if not can_access_employee(
        access=access,
        employee_id=(
            device.employee_id
        ),
    ):
        raise ValidationError(
            "Desktop agent device is outside "
            "your permitted employee scope."
        )

    return device


def require_device_owner(
    *,
    access: LiveMonitoringAccess,
    device: DesktopAgentDevice,
) -> None:
    if (
        access.actor_user_id
        != device.user_id
    ):
        raise ValidationError(
            "Only the registered device user "
            "may respond to this capture request."
        )


__all__ = [
    "LiveMonitoringAccess",
    "resolve_live_monitoring_access",
    "can_access_employee",
    "resolve_device_for_request",
    "require_device_owner",
]