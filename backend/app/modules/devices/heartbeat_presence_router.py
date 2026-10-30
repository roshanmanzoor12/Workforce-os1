from __future__ import annotations

from fastapi import (
    APIRouter,
    Depends,
    status,
)

from app.db.tenant import tenant_session
from app.modules.devices.auth_dependency import (
    get_authenticated_device,
)
from app.modules.devices.auth_service import (
    AuthenticatedDeviceContext,
)
from app.modules.devices.heartbeat_presence_schemas import (
    DevicePresenceResponse,
)
from app.modules.devices.heartbeat_presence_service import (
    DevicePresenceService,
)


__all__ = [
    "router",
]


router = APIRouter(
    prefix="/device-agent",
    tags=["Device Agent"],
)


@router.get(
    "/presence",
    response_model=DevicePresenceResponse,
    status_code=status.HTTP_200_OK,
    summary="Get authenticated device presence",
    name="get_device_presence",
)
async def get_device_presence(
    authenticated_device: AuthenticatedDeviceContext = Depends(
        get_authenticated_device
    ),
) -> DevicePresenceResponse:
    """
    Return server-derived online/offline presence for the
    currently authenticated device.
    """

    async with tenant_session(
        authenticated_device.database_name,
        cluster_key=authenticated_device.cluster_key,
    ) as session:
        service = DevicePresenceService(
            session
        )

        return await service.get_presence(
            device_id=authenticated_device.device_id,
            device_uuid=authenticated_device.device_uuid,
        )