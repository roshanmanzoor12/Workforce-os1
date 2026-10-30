from __future__ import annotations

from fastapi import (
    APIRouter,
    Depends,
    Query,
    status,
)

from app.db.tenant import tenant_session
from app.modules.app_tracking.history_schemas import (
    AppUsageHistoryResponse,
)
from app.modules.app_tracking.history_service import (
    AppTrackingHistoryService,
)
from app.modules.app_tracking.repository import (
    AppTrackingRepository,
)
from app.modules.devices.auth_dependency import (
    get_authenticated_device,
)
from app.modules.devices.auth_service import (
    AuthenticatedDeviceContext,
)


router = APIRouter(
    prefix="/device-agent",
    tags=["Device Agent App Tracking"],
)


@router.get(
    "/app-history",
    response_model=AppUsageHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get authenticated device application history",
    name="get_device_app_history",
)
async def get_device_app_history(
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
    ),
    authenticated_device: AuthenticatedDeviceContext = Depends(
        get_authenticated_device
    ),
) -> AppUsageHistoryResponse:
    async with tenant_session(
        authenticated_device.database_name,
        cluster_key=authenticated_device.cluster_key,
    ) as session:
        repository = AppTrackingRepository(
            session
        )

        service = AppTrackingHistoryService(
            repository
        )

        return await service.list_device_history(
            authenticated_device.device_id,
            limit=limit,
        )


__all__ = [
    "router",
]