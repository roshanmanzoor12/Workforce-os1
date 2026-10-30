from __future__ import annotations

from app.modules.workspace_permissions.permissions import (
    WorkspacePermission,
)


HOLIDAYS_VIEW_PERMISSION = (
    WorkspacePermission
    .HOLIDAYS_VIEW
    .value
)

HOLIDAYS_MANAGE_PERMISSION = (
    WorkspacePermission
    .HOLIDAYS_MANAGE
    .value
)

HOLIDAYS_SELF_READ_PERMISSION = (
    WorkspacePermission
    .HOLIDAYS_SELF_READ
    .value
)

HOLIDAYS_TEAM_READ_PERMISSION = (
    WorkspacePermission
    .HOLIDAYS_TEAM_READ
    .value
)

HOLIDAYS_ALL_READ_PERMISSION = (
    WorkspacePermission
    .HOLIDAYS_ALL_READ
    .value
)


__all__ = [
    "HOLIDAYS_VIEW_PERMISSION",
    "HOLIDAYS_MANAGE_PERMISSION",
    "HOLIDAYS_SELF_READ_PERMISSION",
    "HOLIDAYS_TEAM_READ_PERMISSION",
    "HOLIDAYS_ALL_READ_PERMISSION",
]