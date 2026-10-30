from __future__ import annotations

import logging

from fastapi import (
    APIRouter,
    Depends,
    status,
)

from app.db.tenant import tenant_session
from app.modules.activity.schemas import (
    ActivityStateRequest,
    ActivityStateResponse,
    ActivityStatusResponse,
)
from app.modules.activity.service import (
    ActivityService,
)
from app.modules.devices.auth_dependency import (
    get_authenticated_device,
)
from app.modules.devices.auth_service import (
    AuthenticatedDeviceContext,
)
from app.modules.work_sessions.live_integration import (
    process_persisted_activity_event,
)


__all__ = [
    "router",
]


logger = logging.getLogger(
    __name__
)


router = APIRouter(
    prefix="/device-agent",
    tags=["Device Agent Activity"],
)


# =========================================================
# REPORT ACTIVE / IDLE STATE
# =========================================================

@router.post(
    "/activity-state",
    response_model=ActivityStateResponse,
    status_code=status.HTTP_200_OK,
    summary="Report authenticated device active or idle state",
    name="report_device_activity_state",
)
async def report_device_activity_state(
    payload: ActivityStateRequest,
    authenticated_device: AuthenticatedDeviceContext = Depends(
        get_authenticated_device
    ),
) -> ActivityStateResponse:
    """
    Record one active/idle observation from an authenticated
    WorkforceOS Agent.

    Device identity and tenant routing are derived exclusively from
    authenticated device credentials.

    The request body cannot select:
    - workspace
    - tenant database
    - device UUID
    - employee assignment

    No keystrokes, typed text, clipboard contents, or input content
    are accepted by this endpoint.

    After the activity event is persisted, the same tenant session
    processes that event into the device's current work session.
    """

    async with tenant_session(
        authenticated_device.database_name,
        cluster_key=authenticated_device.cluster_key,
    ) as session:
        activity_service = ActivityService(
            session
        )

        response = await activity_service.record_state(
            device_id=authenticated_device.device_id,
            device_uuid=authenticated_device.device_uuid,
            payload=payload,
        )

        processing_result = (
            await process_persisted_activity_event(
                session,
                response.event_id,
            )
        )

        logger.debug(
            (
                "Processed activity event %s into work session %s. "
                "created=%s closed_previous=%s ignored=%s "
                "state=%s active_seconds=%s idle_seconds=%s"
            ),
            response.event_id,
            processing_result.session_id,
            processing_result.created,
            processing_result.closed_previous_session,
            processing_result.ignored_event,
            processing_result.current_state,
            processing_result.active_seconds,
            processing_result.idle_seconds,
        )

        return response


# =========================================================
# CURRENT DEVICE ACTIVITY STATUS
# =========================================================

@router.get(
    "/activity-status",
    response_model=ActivityStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get authenticated device current activity status",
    name="get_device_activity_status",
)
async def get_device_activity_status(
    authenticated_device: AuthenticatedDeviceContext = Depends(
        get_authenticated_device
    ),
) -> ActivityStatusResponse:
    """
    Return the latest active/idle state for the currently
    authenticated device.

    This endpoint is agent-authenticated and is not intended to be
    called by the web dashboard.
    """

    async with tenant_session(
        authenticated_device.database_name,
        cluster_key=authenticated_device.cluster_key,
    ) as session:
        service = ActivityService(
            session
        )

        return await service.get_device_status(
            device_id=authenticated_device.device_id,
            device_uuid=authenticated_device.device_uuid,
        )