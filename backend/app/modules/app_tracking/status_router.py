from __future__ import annotations

from fastapi import (
    APIRouter,
    Depends,
    status,
)

from app.db.tenant import tenant_session
from app.modules.app_tracking.query_service import (
    AppTrackingQueryService,
)
from app.modules.app_tracking.status_schemas import (
    CurrentAppStatusResponse,
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
    "/app-status",
    response_model=CurrentAppStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get authenticated device foreground application status",
    name="get_device_current_app_status",
)
async def get_device_current_app_status(
    authenticated_device: AuthenticatedDeviceContext = Depends(
        get_authenticated_device
    ),
) -> CurrentAppStatusResponse:
    async with tenant_session(
        authenticated_device.database_name,
        cluster_key=authenticated_device.cluster_key,
    ) as session:
        service = AppTrackingQueryService(
            session
        )

        observation = (
            await service.get_latest_observation(
                authenticated_device.device_id
            )
        )

        if observation is None:
            return CurrentAppStatusResponse(
                device_uuid=(
                    authenticated_device.device_uuid
                ),
                has_observation=False,
            )

        interval = (
            await service.get_current_interval(
                authenticated_device.device_id
            )
        )

        return CurrentAppStatusResponse(
            device_uuid=(
                authenticated_device.device_uuid
            ),
            has_observation=True,
            process_name=(
                observation.process_name
            ),
            executable_path=(
                observation.executable_path
            ),
            window_title=(
                observation.window_title
            ),
            app_key=(
                observation.app_key
            ),
            observed_at=(
                observation.observed_at
            ),
            interval_id=(
                interval.id
                if interval is not None
                else None
            ),
            interval_started_at=(
                interval.started_at
                if interval is not None
                else None
            ),
            duration_seconds=(
                interval.duration_seconds
                if interval is not None
                else None
            ),
        )


__all__ = [
    "router",
]