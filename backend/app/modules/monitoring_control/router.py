from __future__ import annotations

from fastapi import (
    APIRouter,
    status,
)

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
    MonitoringAccessResponse,
    MonitoringControlSummaryResponse,
)
from app.modules.monitoring_control.service import (
    MonitoringControlService,
)


router = APIRouter(
    prefix=(
        "/workspaces/{workspace_id}/"
        "monitoring-control"
    ),
    tags=["Monitoring Control"],
)


def service_from(
    scope: TenantScope,
) -> MonitoringControlService:
    return MonitoringControlService(
        scope
    )


@router.get(
    "",
    response_model=(
        MonitoringControlSummaryResponse
    ),
    status_code=status.HTTP_200_OK,
    summary="Get monitoring control summary",
)
async def monitoring_control_summary(
    scope: TenantScope,
) -> MonitoringControlSummaryResponse:
    service = service_from(
        scope
    )

    service.require_monitoring_view()

    return service.summary()


@router.get(
    "/live-access",
    response_model=MonitoringAccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Check live monitoring access",
)
async def live_monitoring_access(
    scope: TenantScope,
) -> MonitoringAccessResponse:
    service = service_from(
        scope
    )

    service.require_live_screen_view()

    return MonitoringAccessResponse(
        permission=(
            MONITORING_LIVE_VIEW_PERMISSION
        ),
        allowed=True,
    )


@router.get(
    "/manage-access",
    response_model=MonitoringAccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Check monitoring management access",
)
async def monitoring_manage_access(
    scope: TenantScope,
) -> MonitoringAccessResponse:
    service = service_from(
        scope
    )

    service.require_monitoring_manage()

    return MonitoringAccessResponse(
        permission=(
            MONITORING_MANAGE_PERMISSION
        ),
        allowed=True,
    )


@router.get(
    "/settings-access",
    response_model=MonitoringAccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Check monitoring settings access",
)
async def monitoring_settings_access(
    scope: TenantScope,
) -> MonitoringAccessResponse:
    service = service_from(
        scope
    )

    service.require_settings_manage()

    return MonitoringAccessResponse(
        permission=(
            MONITORING_SETTINGS_MANAGE_PERMISSION
        ),
        allowed=True,
    )


@router.get(
    "/view-access",
    response_model=MonitoringAccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Check monitoring view access",
)
async def monitoring_view_access(
    scope: TenantScope,
) -> MonitoringAccessResponse:
    service = service_from(
        scope
    )

    service.require_monitoring_view()

    return MonitoringAccessResponse(
        permission=(
            MONITORING_VIEW_PERMISSION
        ),
        allowed=True,
    )


__all__ = [
    "router",
]