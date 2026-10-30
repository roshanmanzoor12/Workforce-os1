from __future__ import annotations

from app.modules.workspace_permissions.permissions import (
    WorkspacePermission,
)


SHIFT_VIEW_PERMISSION = (
    WorkspacePermission.SHIFTS_VIEW.value
)

SHIFT_MANAGE_PERMISSION = (
    WorkspacePermission.SHIFTS_MANAGE.value
)

SHIFT_SELF_READ_PERMISSION = (
    WorkspacePermission.SHIFTS_SELF_READ.value
)

SHIFT_TEAM_READ_PERMISSION = (
    WorkspacePermission.SHIFTS_TEAM_READ.value
)

SHIFT_ALL_READ_PERMISSION = (
    WorkspacePermission.SHIFTS_ALL_READ.value
)


__all__ = [
    "SHIFT_VIEW_PERMISSION",
    "SHIFT_MANAGE_PERMISSION",
    "SHIFT_SELF_READ_PERMISSION",
    "SHIFT_TEAM_READ_PERMISSION",
    "SHIFT_ALL_READ_PERMISSION",
]