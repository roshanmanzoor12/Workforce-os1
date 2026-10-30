from __future__ import annotations

from fastapi import (
    APIRouter,
    Depends,
    status,
)

from sqlalchemy import select
from app.db.tenant import tenant_session
from app.modules.devices.models import Device
from app.modules.app_tracking.coordinator import (
    AppTrackingCoordinator,
)
from app.modules.app_tracking.privacy import (
    AppTrackingPrivacyPolicy,
)
from app.modules.app_tracking.schemas import (
    AppObservationRequest,
    AppObservationResponse,
)
from app.modules.devices.auth_dependency import (
    get_authenticated_device,
)
from app.modules.devices.auth_service import (
    AuthenticatedDeviceContext,
)


__all__ = [
    "router",
]


router = APIRouter(
    prefix="/device-agent",
    tags=["Device Agent App Tracking"],
)


@router.post(
    "/app-observation",
    response_model=AppObservationResponse,
    status_code=status.HTTP_200_OK,
    summary="Report foreground application observation",
    name="report_device_app_observation",
)
async def report_device_app_observation(
    payload: AppObservationRequest,
    authenticated_device: AuthenticatedDeviceContext = Depends(
        get_authenticated_device
    ),
) -> AppObservationResponse:
    """
    Record the foreground application observed by an authenticated
    WorkforceOS Agent.

    Device and tenant identity are derived exclusively from the
    authenticated device credential.

    This endpoint does not accept keystrokes, clipboard content,
    passwords, mouse coordinates, or typed input.
    """

    privacy = AppTrackingPrivacyPolicy(
        capture_window_titles=False
    )

    sanitized_payload = AppObservationRequest(
        process_name=payload.process_name,
        executable_path=(
            privacy.sanitize_executable_path(
                payload.executable_path
            )
        ),
        window_title=(
            privacy.sanitize_window_title(
                payload.window_title
            )
        ),
        observed_at=payload.observed_at,
    )

    async with tenant_session(
        authenticated_device.database_name,
        cluster_key=authenticated_device.cluster_key,
    ) as session:
        # Resolve attribution from the authenticated tenant-local device.
        # Never accept employee identity from an Agent request payload.
        assigned_employee_id = await session.scalar(
            select(Device.employee_id).where(
                Device.id == authenticated_device.device_id,
                Device.device_uuid == authenticated_device.device_uuid,
            )
        )

        coordinator = AppTrackingCoordinator(
            session
        )

        return await coordinator.record_observation(
            device_id=authenticated_device.device_id,
            device_uuid=authenticated_device.device_uuid,
            employee_id=assigned_employee_id,
            payload=sanitized_payload,
        )