from __future__ import annotations

from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    status,
)
from sqlalchemy import select

from app.modules.devices.models import Device

from app.db.tenant import (
    tenant_session,
)
from app.modules.devices.auth_dependency import (
    get_authenticated_device,
)
from app.modules.devices.auth_service import (
    AuthenticatedDeviceContext,
)
from app.modules.website_tracking.coordinator import (
    WebsiteTrackingCoordinator,
)
from app.modules.website_tracking.privacy import (
    WebsiteTrackingPrivacyPolicy,
)
from app.modules.website_tracking.schemas import (
    WebsiteObservationProcessingResult,
    WebsiteObservationRequest,
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


@router.post(
    "/device-agent/website-observation",
    response_model=WebsiteObservationProcessingResult,
    status_code=status.HTTP_200_OK,
    summary=(
        "Report foreground website observation"
    ),
)
async def report_device_website_observation(
    payload: WebsiteObservationRequest,
    authenticated_device: AuthenticatedDevice,
) -> WebsiteObservationProcessingResult:
    """
    Record one website/domain observation.

    Security properties:

    - device identity comes from authenticated credentials
    - tenant selection comes from trusted server routing
    - request cannot choose workspace/database
    - request cannot choose device UUID
    - employee identity is not accepted from the agent

    Privacy defaults:

    - domain is retained
    - full URL is suppressed
    - page title is suppressed
    - query strings are never retained here
    """

    privacy_policy = (
        WebsiteTrackingPrivacyPolicy(
            capture_page_urls=False,
            capture_page_titles=False,
        )
    )

    async with tenant_session(
        authenticated_device.database_name
    ) as session:
        coordinator = (
            WebsiteTrackingCoordinator(
                session,
                privacy_policy=privacy_policy,
            )
        )

        # Resolve the employee from the authenticated tenant-local device.
        # Never accept employee identity from a client-supplied observation.
        employee_id = await session.scalar(
            select(Device.employee_id).where(
                Device.id == authenticated_device.device_id
            )
        )

        return await coordinator.record_observation(
            device_id=(
                authenticated_device.device_id
            ),
            employee_id=employee_id,
            request=payload,
        )


__all__ = [
    "router",
    "report_device_website_observation",
]