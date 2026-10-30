from __future__ import annotations

from app.modules.workspace_permissions.permissions import (
    WorkspacePermission,
)


# =========================================================
# CANONICAL MONITORING PERMISSIONS
# =========================================================


MONITORING_VIEW_PERMISSION = (
    WorkspacePermission
    .MONITORING_VIEW
    .value
)

MONITORING_MANAGE_PERMISSION = (
    WorkspacePermission
    .MONITORING_MANAGE
    .value
)

MONITORING_LIVE_VIEW_PERMISSION = (
    WorkspacePermission
    .MONITORING_LIVE_VIEW
    .value
)

MONITORING_SETTINGS_MANAGE_PERMISSION = (
    WorkspacePermission
    .MONITORING_SETTINGS_MANAGE
    .value
)


# =========================================================
# MONITORING CONTROL PERMISSION SET
# =========================================================


MONITORING_CONTROL_PERMISSIONS = frozenset(
    {
        MONITORING_VIEW_PERMISSION,
        MONITORING_MANAGE_PERMISSION,
        MONITORING_LIVE_VIEW_PERMISSION,
        MONITORING_SETTINGS_MANAGE_PERMISSION,
    }
)


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "MONITORING_VIEW_PERMISSION",
    "MONITORING_MANAGE_PERMISSION",
    "MONITORING_LIVE_VIEW_PERMISSION",
    "MONITORING_SETTINGS_MANAGE_PERMISSION",
    "MONITORING_CONTROL_PERMISSIONS",
]