from __future__ import annotations

from app.db.tenant_dependency import (
    TenantScope,
)
from app.modules.monitoring_control.permissions import (
    MONITORING_LIVE_VIEW_PERMISSION,
    MONITORING_MANAGE_PERMISSION,
    MONITORING_SETTINGS_MANAGE_PERMISSION,
    MONITORING_VIEW_PERMISSION,
)
from app.modules.monitoring_control.schemas import (
    MonitoringCapabilityResponse,
    MonitoringControlSummaryResponse,
)
from app.modules.workspace_permissions.service import (
    WorkspacePermissionService,
)
from app.modules.workspace_permissions.tenant_scope import (
    get_scope_role,
)


class MonitoringControlService:
    """
    Permission-oriented Monitoring Control Center service.

    This layer does not collect monitoring data.

    It only determines what the authenticated workspace member
    is authorized to view or manage.
    """

    def __init__(
        self,
        scope: TenantScope,
    ) -> None:
        self.scope = scope

        self.permissions = (
            WorkspacePermissionService(
                scope
            )
        )

    def summary(
        self,
    ) -> MonitoringControlSummaryResponse:
        role_key = get_scope_role(
            self.scope
        )

        if role_key is None:
            role_key = "unknown"

        relevant_permissions = [
            permission
            for permission
            in self.permissions
            .list_permissions()
            if permission.startswith(
                "monitoring."
            )
        ]

        return MonitoringControlSummaryResponse(
            role_key=role_key,
            capabilities=(
                MonitoringCapabilityResponse(
                    monitoring_view=(
                        self.permissions
                        .has_permission(
                            MONITORING_VIEW_PERMISSION
                        )
                    ),
                    monitoring_manage=(
                        self.permissions
                        .has_permission(
                            MONITORING_MANAGE_PERMISSION
                        )
                    ),
                    live_screen_view=(
                        self.permissions
                        .has_permission(
                            MONITORING_LIVE_VIEW_PERMISSION
                        )
                    ),
                    settings_manage=(
                        self.permissions
                        .has_permission(
                            MONITORING_SETTINGS_MANAGE_PERMISSION
                        )
                    ),
                )
            ),
            permissions=sorted(
                relevant_permissions
            ),
        )

    def require_monitoring_view(
        self,
    ) -> None:
        self.permissions.require(
            MONITORING_VIEW_PERMISSION
        )

    def require_monitoring_manage(
        self,
    ) -> None:
        self.permissions.require(
            MONITORING_MANAGE_PERMISSION
        )

    def require_live_screen_view(
        self,
    ) -> None:
        self.permissions.require(
            MONITORING_LIVE_VIEW_PERMISSION
        )

    def require_settings_manage(
        self,
    ) -> None:
        self.permissions.require(
            MONITORING_SETTINGS_MANAGE_PERMISSION
        )


__all__ = [
    "MonitoringControlService",
]