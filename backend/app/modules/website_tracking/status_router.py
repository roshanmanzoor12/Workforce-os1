from __future__ import annotations

from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
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
from app.modules.website_tracking.query_service import (
    WebsiteTrackingQueryService,
)
from app.modules.website_tracking.repository import (
    WebsiteTrackingRepository,
)
from app.modules.website_tracking.status_schemas import (
    CurrentWebsiteStatusResponse,
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
    "/device-agent/website-status",
    response_model=CurrentWebsiteStatusResponse,
    status_code=status.HTTP_200_OK,
    summary=(
        "Get authenticated device current website status"
    ),
)
async def get_device_current_website_status(
    authenticated_device: AuthenticatedDevice,
) -> CurrentWebsiteStatusResponse:
    """
    Return the currently open website interval belonging to
    the authenticated endpoint.

    This is an agent diagnostic endpoint.

    Browser dashboard/admin clients should not use device secrets.
    A separate browser-facing aggregation API will be added in the
    Platform/Core SaaS phase.
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
            WebsiteTrackingQueryService(
                repository
            )
        )

        return await service.get_current_status(
            device_id=(
                authenticated_device.device_id
            )
        )


__all__ = [
    "router",
    "get_device_current_website_status",
]