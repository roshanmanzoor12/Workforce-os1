from __future__ import annotations

from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Query,
    status,
)

from app.db.tenant import (
    tenant_session,
)
from app.modules.devices.auth_dependency import (
    get_authenticated_device,
)
from app.modules.devices.auth_service import (
    AuthenticatedDeviceContext,
)
from app.modules.website_tracking.history_schemas import (
    WebsiteUsageHistoryResponse,
)
from app.modules.website_tracking.history_service import (
    WebsiteTrackingHistoryService,
)
from app.modules.website_tracking.repository import (
    WebsiteTrackingRepository,
)


router = APIRouter(
    tags=[
        "Device Agent Website Tracking",
    ],
)


AuthenticatedDevice = Annotated[
    AuthenticatedDeviceContext,
    Depends(
        get_authenticated_device
    ),
]


@router.get(
    "/device-agent/website-history",
    response_model=WebsiteUsageHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary=(
        "Get authenticated device website history"
    ),
)
async def get_device_website_history(
    authenticated_device: AuthenticatedDevice,
    limit: int = Query(
        default=100,
        ge=1,
        le=5000,
    ),
) -> WebsiteUsageHistoryResponse:
    """
    Return recent website/domain usage intervals belonging only
    to the authenticated device.
    """

    async with tenant_session(
        authenticated_device.database_name
    ) as session:
        repository = (
            WebsiteTrackingRepository(
                session
            )
        )

        service = (
            WebsiteTrackingHistoryService(
                repository
            )
        )

        return await service.list_device_history(
            device_id=(
                authenticated_device.device_id
            ),
            limit=limit,
        )


__all__ = [
    "router",
    "get_device_website_history",
]