from __future__ import annotations

import uuid
from datetime import datetime
from typing import (
    Annotated,
    Any,
)

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)

from app.core.exceptions import (
    ValidationError,
)
from app.modules.live_monitoring.access import (
    resolve_live_monitoring_access,
)
from app.modules.live_monitoring.schemas import (
    LiveMonitoringCapabilitiesResponse,
    LiveScreenActivateRequest,
    LiveScreenDecision,
    LiveScreenEndRequest,
    LiveScreenRequestCreate,
    LiveScreenResponse,
    ScreenshotAgentComplete,
    ScreenshotAgentDeny,
    ScreenshotAgentFail,
    ScreenshotListResponse,
    ScreenshotMediaResponse,
    ScreenshotRequestCreate,
    ScreenshotResponse,
)
from app.modules.live_monitoring.phase17 import (
    SCREENSHOT_ALLOWED_STATUSES,
    create_screenshot_download_url,
    effective_retention_start,
    record_screenshot_audit,
)
from app.modules.monitoring_admin.service import (
    MonitoringAdminService,
)
from app.modules.live_monitoring.service import (
    LiveMonitoringNotFoundError,
    LiveMonitoringPermissionError,
    LiveMonitoringService,
)
from app.modules.tenant_api.dependencies import (
    get_authorized_tenant_context,
)


router = APIRouter(
    prefix=(
        "/workspaces/"
        "{workspace_id}/live-monitoring"
    ),
    tags=[
        "live-monitoring",
    ],
)


TenantContext = Annotated[
    Any,
    Depends(
        get_authorized_tenant_context
    ),
]


async def _access(
    *,
    workspace_id: uuid.UUID,
    context: Any,
):
    return await (
        resolve_live_monitoring_access(
            workspace_id=workspace_id,
            context=context,
        )
    )


def _service(
    context: Any,
) -> LiveMonitoringService:
    return LiveMonitoringService(
        context.tenant_session
    )


def _http_error(
    exc: Exception,
) -> HTTPException:
    if isinstance(
        exc,
        LiveMonitoringNotFoundError,
    ):
        return HTTPException(
            status_code=404,
            detail=str(
                exc
            ),
        )

    if isinstance(
        exc,
        LiveMonitoringPermissionError,
    ):
        return HTTPException(
            status_code=403,
            detail=str(
                exc
            ),
        )

    if isinstance(
        exc,
        ValidationError,
    ):
        return HTTPException(
            status_code=422,
            detail=str(
                exc
            ),
        )

    raise exc


@router.post(
    "/screenshots",
    response_model=ScreenshotResponse,
)
async def request_screenshot(
    workspace_id: uuid.UUID,
    payload: ScreenshotRequestCreate,
    context: TenantContext,
) -> ScreenshotResponse:
    access = await _access(
        workspace_id=workspace_id,
        context=context,
    )

    try:
        return await (
            _service(
                context
            )
            .request_screenshot(
                access=access,
                payload=payload,
            )
        )

    except (
        ValidationError,
        LiveMonitoringNotFoundError,
        LiveMonitoringPermissionError,
    ) as exc:
        raise _http_error(
            exc
        ) from exc


@router.get(
    "/screenshots",
    response_model=ScreenshotListResponse,
)
async def list_screenshots(
    workspace_id: uuid.UUID,
    context: TenantContext,

    employee_id: uuid.UUID | None = Query(
        default=None,
    ),

    device_id: uuid.UUID | None = Query(
        default=None,
    ),

    status_filter: str | None = Query(
        default=None,
        alias="status",
        max_length=32,
    ),

    start_at: datetime | None = Query(
        default=None,
    ),

    end_at: datetime | None = Query(
        default=None,
    ),

    limit: int = Query(
        default=100,
        ge=1,
        le=500,
    ),

    offset: int = Query(
        default=0,
        ge=0,
    ),
) -> ScreenshotListResponse:
    access = await _access(
        workspace_id=workspace_id,
        context=context,
    )

    if status_filter is not None:
        status_filter = (
            status_filter
            .strip()
            .lower()
        )

        if (
            status_filter
            not in SCREENSHOT_ALLOWED_STATUSES
        ):
            raise HTTPException(
                status_code=422,
                detail=(
                    "Invalid screenshot status."
                ),
            )

    policy = await (
        MonitoringAdminService(
            tenant_session=(
                context.tenant_session
            ),
            workspace_id=workspace_id,
        )
        .policy()
    )

    effective_start = (
        effective_retention_start(
            requested_start=start_at,
            retention_days=(
                policy
                .screenshot_retention_days
            ),
        )
    )

    try:
        result = await (
            _service(
                context
            )
            .list_screenshots_history(
                access=access,
                employee_id=employee_id,
                device_id=device_id,
                status=status_filter,
                start_at=effective_start,
                end_at=end_at,
                limit=limit,
                offset=offset,
            )
        )

        await record_screenshot_audit(
            control_session=(
                context.control_session
            ),
            workspace_id=workspace_id,
            actor_user_id=(
                access.actor_user_id
            ),
            action=(
                "screenshot.history.view"
            ),
            event_data={
                "employee_id": employee_id,
                "device_id": device_id,
                "status": status_filter,
                "start_at": effective_start,
                "end_at": end_at,
                "result_count": len(
                    result.items
                ),
            },
        )

        return result

    except (
        ValidationError,
        LiveMonitoringPermissionError,
    ) as exc:
        raise _http_error(
            exc
        ) from exc


@router.post(
    "/screenshots/{request_id}/complete",
    response_model=ScreenshotResponse,
)
async def complete_screenshot(
    workspace_id: uuid.UUID,
    request_id: uuid.UUID,
    payload: ScreenshotAgentComplete,
    context: TenantContext,
) -> ScreenshotResponse:
    access = await _access(
        workspace_id=workspace_id,
        context=context,
    )

    try:
        return await (
            _service(
                context
            )
            .complete_screenshot(
                access=access,
                request_id=request_id,
                payload=payload,
            )
        )

    except (
        ValidationError,
        LiveMonitoringNotFoundError,
        LiveMonitoringPermissionError,
    ) as exc:
        raise _http_error(
            exc
        ) from exc


@router.post(
    "/screenshots/{request_id}/deny",
    response_model=ScreenshotResponse,
)
async def deny_screenshot(
    workspace_id: uuid.UUID,
    request_id: uuid.UUID,
    payload: ScreenshotAgentDeny,
    context: TenantContext,
) -> ScreenshotResponse:
    access = await _access(
        workspace_id=workspace_id,
        context=context,
    )

    try:
        return await (
            _service(
                context
            )
            .deny_screenshot(
                access=access,
                request_id=request_id,
                payload=payload,
            )
        )

    except (
        ValidationError,
        LiveMonitoringNotFoundError,
        LiveMonitoringPermissionError,
    ) as exc:
        raise _http_error(
            exc
        ) from exc


@router.post(
    "/screenshots/{request_id}/fail",
    response_model=ScreenshotResponse,
)
async def fail_screenshot(
    workspace_id: uuid.UUID,
    request_id: uuid.UUID,
    payload: ScreenshotAgentFail,
    context: TenantContext,
) -> ScreenshotResponse:
    access = await _access(
        workspace_id=workspace_id,
        context=context,
    )

    try:
        return await (
            _service(
                context
            )
            .fail_screenshot(
                access=access,
                request_id=request_id,
                payload=payload,
            )
        )

    except (
        ValidationError,
        LiveMonitoringNotFoundError,
        LiveMonitoringPermissionError,
    ) as exc:
        raise _http_error(
            exc
        ) from exc


@router.post(
    "/screenshots/{request_id}/media",
    response_model=ScreenshotMediaResponse,
)
async def screenshot_media(
    workspace_id: uuid.UUID,
    request_id: uuid.UUID,
    context: TenantContext,
) -> ScreenshotMediaResponse:
    access = await _access(
        workspace_id=workspace_id,
        context=context,
    )

    try:
        object_key = await (
            _service(
                context
            )
            .get_screenshot_media_object_key(
                access=access,
                request_id=request_id,
            )
        )

        (
            download_url,
            expires_in_seconds,
        ) = create_screenshot_download_url(
            object_key=object_key
        )

        await record_screenshot_audit(
            control_session=(
                context.control_session
            ),
            workspace_id=workspace_id,
            actor_user_id=(
                access.actor_user_id
            ),
            action=(
                "screenshot.media.view"
            ),
            target_id=request_id,
        )

        return ScreenshotMediaResponse(
            request_id=request_id,
            download_url=download_url,
            expires_in_seconds=(
                expires_in_seconds
            ),
        )

    except (
        ValidationError,
        LiveMonitoringNotFoundError,
        LiveMonitoringPermissionError,
    ) as exc:
        raise _http_error(
            exc
        ) from exc


@router.post(
    "/live-sessions",
    response_model=LiveScreenResponse,
)
async def request_live_screen(
    workspace_id: uuid.UUID,
    payload: LiveScreenRequestCreate,
    context: TenantContext,
) -> LiveScreenResponse:
    access = await _access(
        workspace_id=workspace_id,
        context=context,
    )

    try:
        return await (
            _service(
                context
            )
            .request_live_screen(
                access=access,
                payload=payload,
            )
        )

    except (
        ValidationError,
        LiveMonitoringNotFoundError,
        LiveMonitoringPermissionError,
    ) as exc:
        raise _http_error(
            exc
        ) from exc


@router.post(
    "/live-sessions/{session_id}/decision",
    response_model=LiveScreenResponse,
)
async def decide_live_screen(
    workspace_id: uuid.UUID,
    session_id: uuid.UUID,
    payload: LiveScreenDecision,
    context: TenantContext,
) -> LiveScreenResponse:
    access = await _access(
        workspace_id=workspace_id,
        context=context,
    )

    try:
        return await (
            _service(
                context
            )
            .decide_live_screen(
                access=access,
                session_id=session_id,
                payload=payload,
            )
        )

    except (
        ValidationError,
        LiveMonitoringNotFoundError,
        LiveMonitoringPermissionError,
    ) as exc:
        raise _http_error(
            exc
        ) from exc


@router.post(
    "/live-sessions/{session_id}/activate",
    response_model=LiveScreenResponse,
)
async def activate_live_screen(
    workspace_id: uuid.UUID,
    session_id: uuid.UUID,
    payload: LiveScreenActivateRequest,
    context: TenantContext,
) -> LiveScreenResponse:
    access = await _access(
        workspace_id=workspace_id,
        context=context,
    )

    try:
        return await (
            _service(
                context
            )
            .activate_live_screen(
                access=access,
                session_id=session_id,
                payload=payload,
            )
        )

    except (
        ValidationError,
        LiveMonitoringNotFoundError,
        LiveMonitoringPermissionError,
    ) as exc:
        raise _http_error(
            exc
        ) from exc


@router.post(
    "/live-sessions/{session_id}/end",
    response_model=LiveScreenResponse,
)
async def end_live_screen(
    workspace_id: uuid.UUID,
    session_id: uuid.UUID,
    payload: LiveScreenEndRequest,
    context: TenantContext,
) -> LiveScreenResponse:
    access = await _access(
        workspace_id=workspace_id,
        context=context,
    )

    try:
        return await (
            _service(
                context
            )
            .end_live_screen(
                access=access,
                session_id=session_id,
                payload=payload,
            )
        )

    except (
        ValidationError,
        LiveMonitoringNotFoundError,
        LiveMonitoringPermissionError,
    ) as exc:
        raise _http_error(
            exc
        ) from exc


@router.get(
    "/live-sessions/{session_id}",
    response_model=LiveScreenResponse,
)
async def get_live_screen(
    workspace_id: uuid.UUID,
    session_id: uuid.UUID,
    context: TenantContext,
) -> LiveScreenResponse:
    access = await _access(
        workspace_id=workspace_id,
        context=context,
    )

    try:
        return await (
            _service(
                context
            )
            .get_live_screen(
                access=access,
                session_id=session_id,
            )
        )

    except (
        ValidationError,
        LiveMonitoringNotFoundError,
        LiveMonitoringPermissionError,
    ) as exc:
        raise _http_error(
            exc
        ) from exc


@router.get(
    "/capabilities",
    response_model=(
        LiveMonitoringCapabilitiesResponse
    ),
)
async def live_monitoring_capabilities(
    workspace_id: uuid.UUID,
    context: TenantContext,
) -> LiveMonitoringCapabilitiesResponse:
    await _access(
        workspace_id=workspace_id,
        context=context,
    )

    return (
        LiveMonitoringService
        .capabilities()
    )


__all__ = [
    "router",
]

# NATIVE_HTTP_GATEWAY_V1: authenticated owner snapshot, never raw token access.
import base64 as _native_base64
from datetime import datetime as _native_datetime, timezone as _native_timezone
from app.modules.live_monitoring.models import LiveScreenSession as _NativeSession
from app.modules.live_monitoring.native_http_gateway import snapshot as _native_snapshot
from app.modules.live_monitoring.native_http_gateway import revoke as _native_revoke
from app.modules.live_monitoring.native_frame_relay import RelayError as _NativeRelayError

@router.get("/live-sessions/{session_id}/native-frame")
async def native_frame_for_owner(
    workspace_id: uuid.UUID, session_id: uuid.UUID, context: TenantContext,
    after: int = Query(default=0, ge=0),
):
    access = await _access(workspace_id=workspace_id, context=context)
    item = await context.tenant_session.get(_NativeSession, session_id)
    if item is None or item.requested_by_user_id != access.actor_user_id or not access.can_request_live_screen:
        raise HTTPException(status_code=403, detail="Not authorized for this session")
    now = _native_datetime.now(_native_timezone.utc)
    if item.status != "active" or item.expires_at <= now:
        await _native_revoke(str(workspace_id), str(session_id))
        return {"status": "inactive", "sequence": after, "jpeg_base64": None}
    ttl = max(1, int((item.expires_at - now).total_seconds()))
    try:
        seq, frame = await _native_snapshot(str(workspace_id), str(session_id), str(item.employee_id),
            str(item.device_id), ttl, after)
    except _NativeRelayError:
        raise HTTPException(status_code=409, detail="Native media unavailable")
    return {"status": "active", "sequence": seq,
            "jpeg_base64": _native_base64.b64encode(frame).decode("ascii") if frame else None}
