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
from app.modules.devices.heartbeat_schemas import (
    DeviceHeartbeatRequest,
    DeviceHeartbeatResponse,
)
from app.modules.devices.heartbeat_service import (
    DeviceHeartbeatService,
)


__all__ = [
    "router",
]


router = APIRouter(
    prefix="/device-agent",
    tags=["Device Agent"],
)


@router.post(
    "/heartbeat",
    response_model=DeviceHeartbeatResponse,
    status_code=status.HTTP_200_OK,
    summary="Send authenticated device heartbeat",
    name="device_heartbeat",
)
async def device_heartbeat(
    payload: DeviceHeartbeatRequest,
    authenticated_device: AuthenticatedDeviceContext = Depends(
        get_authenticated_device
    ),
) -> DeviceHeartbeatResponse:
    """
    Record one authenticated WorkforceOS Agent heartbeat.

    Device identity and tenant routing come exclusively from
    authenticated device credentials.
    """

    async with tenant_session(
        authenticated_device.database_name,
        cluster_key=authenticated_device.cluster_key,
    ) as session:
        service = DeviceHeartbeatService(
            session
        )

        return await service.record_heartbeat(
            device_id=authenticated_device.device_id,
            device_uuid=authenticated_device.device_uuid,
            payload=payload,
        )