from __future__ import annotations

from fastapi import (
    APIRouter,
    status,
    HTTPException,
)

from app.modules.devices.agent_schemas import (
    DeviceAgentIdentityResponse,
)
from app.modules.devices.auth_dependency import (
    AuthenticatedDevice,
)


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    prefix="/device-agent",
    tags=["Device Agent"],
)


# =========================================================
# AUTHENTICATED DEVICE IDENTITY
# =========================================================


@router.get(
    "/me",
    response_model=DeviceAgentIdentityResponse,
    status_code=status.HTTP_200_OK,
    summary="Get authenticated device identity",
)
async def get_authenticated_device(
    authenticated_device: AuthenticatedDevice,
) -> DeviceAgentIdentityResponse:
    """
    Verify device credentials and return the endpoint's safe
    authenticated identity.

    Authentication is performed by AuthenticatedDevice dependency:

        X-Device-UUID
        X-Device-Secret
            â†“
        DeviceRoute
            â†“
        trusted workspace
            â†“
        trusted tenant database
            â†“
        DeviceCredential
            â†“
        tenant Device

    This response intentionally does not expose:

        workspace_id
        tenant database name
        cluster key
        credential_id
        secret hash
        device secret
    """

    return DeviceAgentIdentityResponse(
        authenticated=True,
        device_uuid=(
            authenticated_device.device_uuid
        ),
        credential_version=(
            authenticated_device.credential_version
        ),
    )


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "get_authenticated_device",
    "router",
]

import uuid


# =========================================================
# DEVICE-AUTHENTICATED LIVE SESSION INBOX (READ ONLY)
# The authenticated credential determines the workspace and device.
# No client-supplied device ID, employee ID or tenant routing is trusted.
# An inbox item is NOT an authorization lease or permission to capture.
# =========================================================
from datetime import datetime, timezone
from pydantic import BaseModel
from fastapi import Depends
from sqlalchemy import select
from app.db.tenant import tenant_session
from app.modules.devices.auth_dependency import get_authenticated_device
from app.modules.devices.auth_service import AuthenticatedDeviceContext
from app.modules.live_monitoring.models import LiveScreenSession
from app.modules.desktop_agent.models import DesktopAgentDevice
from app.modules.monitoring.models import MonitoringConsent


class DeviceLiveInboxItem(BaseModel):
    session_id: uuid.UUID
    status: str
    expires_at: datetime
    consent_required: bool
    visible_indicator_required: bool


async def _desktop_id_for_authenticated_device(session, authenticated_device):
    desktop = await session.scalar(select(DesktopAgentDevice).where(
        DesktopAgentDevice.installation_id == authenticated_device.device_uuid
    ))
    return desktop


class DeviceLiveInboxResponse(BaseModel):
    sessions: list[DeviceLiveInboxItem]
    capture_authorized: bool = False
    consent_granted: bool = False


@router.get(
    "/live-screen/inbox",
    response_model=DeviceLiveInboxResponse,
    summary="Read live-screen session requests for this authenticated device",
)
async def get_device_live_screen_inbox(
    authenticated_device: AuthenticatedDeviceContext = Depends(get_authenticated_device),
) -> DeviceLiveInboxResponse:
    """Read-only; no media grant, no employee consent assertion, no activation."""
    async with tenant_session(
        authenticated_device.database_name,
        cluster_key=authenticated_device.cluster_key,
    ) as session:
        desktop = await _desktop_id_for_authenticated_device(session, authenticated_device)
        if desktop is None:
            return DeviceLiveInboxResponse(sessions=[], capture_authorized=False, consent_granted=False)
        result = await session.execute(
            select(LiveScreenSession)
            .where(LiveScreenSession.device_id == desktop.id)
            .where(LiveScreenSession.status.in_(("requested", "accepted", "active")))
            .where(LiveScreenSession.expires_at > datetime.now(timezone.utc))
            .order_by(LiveScreenSession.created_at.desc())
            .limit(20)
        )
        items = list(result.scalars().all())
        consent_granted = False
        if desktop is not None:
            consent_granted = bool(await session.scalar(select(MonitoringConsent.id).where(
                MonitoringConsent.user_id == desktop.user_id,
                MonitoringConsent.granted.is_(True),
                MonitoringConsent.revoked_at.is_(None),
            )))
        return DeviceLiveInboxResponse(
            sessions=[
                DeviceLiveInboxItem(
                    session_id=item.id,
                    status=item.status,
                    expires_at=item.expires_at,
                    consent_required=item.consent_required,
                    visible_indicator_required=item.visible_indicator_required,
                )
                for item in items
            ],
            capture_authorized=any(item.status == "active" for item in items),
            consent_granted=consent_granted,
        )


class DeviceLiveDecision(BaseModel):
    accepted: bool
    visible_indicator_shown: bool = False


@router.post("/live-screen/{session_id}/decision")
async def decide_device_live_screen(
    session_id: uuid.UUID,
    payload: DeviceLiveDecision,
    authenticated_device: AuthenticatedDeviceContext = Depends(get_authenticated_device),
):
    async with tenant_session(
        authenticated_device.database_name,
        cluster_key=authenticated_device.cluster_key,
    ) as session:
        item = await session.scalar(select(LiveScreenSession).where(
            LiveScreenSession.id == session_id,
            LiveScreenSession.device_id == (await _desktop_id_for_authenticated_device(session, authenticated_device)).id,
        ))
        now = datetime.now(timezone.utc)
        if item is None or item.expires_at <= now or item.status != "requested":
            raise HTTPException(status_code=409, detail="Live-screen request is no longer available")
        if payload.accepted:
            if not payload.visible_indicator_shown:
                raise HTTPException(status_code=422, detail="Visible indicator must be shown before acceptance")
            item.status = "accepted"
            item.accepted_at = now
        else:
            item.status = "denied"
            item.ended_at = now
            item.end_reason = "employee_rejected"
        await session.commit()
        return {"session_id": str(item.id), "status": item.status}


# WFOS_V9_EMPLOYEE_STOP_REVOCATION
@router.post("/live-screen/{session_id}/stop")
async def stop_device_live_screen(
    session_id: uuid.UUID,
    authenticated_device: AuthenticatedDeviceContext = Depends(get_authenticated_device),
):
    """Employee-initiated revocation, scoped to the authenticated device."""
    async with tenant_session(
        authenticated_device.database_name,
        cluster_key=authenticated_device.cluster_key,
    ) as session:
        desktop = await _desktop_id_for_authenticated_device(session, authenticated_device)
        if desktop is None:
            raise HTTPException(status_code=404, detail="Assigned desktop device not found")
        item = await session.scalar(
            select(LiveScreenSession)
            .where(LiveScreenSession.id == session_id, LiveScreenSession.device_id == desktop.id)
            .with_for_update()
        )
        if item is None:
            raise HTTPException(status_code=404, detail="Live screen session not found")
        if item.status not in {"ended", "denied", "expired"}:
            item.status = "ended"
            item.ended_at = datetime.now(timezone.utc)
            item.end_reason = "employee_stop_sharing"
            await session.commit()
    # A stale relay lease must not serve frames after explicit revocation.
    from app.modules.live_monitoring.native_http_gateway import revoke as revoke_native
    await revoke_native(str(authenticated_device.workspace_id), str(session_id))
    return {"session_id": str(session_id), "status": "ended"}


@router.post("/live-screen/{session_id}/activate")
async def activate_device_live_screen(
    session_id: uuid.UUID,
    authenticated_device: AuthenticatedDeviceContext = Depends(get_authenticated_device),
):
    async with tenant_session(
        authenticated_device.database_name,
        cluster_key=authenticated_device.cluster_key,
    ) as session:
        item = await session.scalar(select(LiveScreenSession).where(
            LiveScreenSession.id == session_id,
            LiveScreenSession.device_id == (await _desktop_id_for_authenticated_device(session, authenticated_device)).id,
        ))
        now = datetime.now(timezone.utc)
        if item is None or item.expires_at <= now or item.status != "accepted":
            raise HTTPException(status_code=409, detail="Session must be accepted before activation")
        item.status = "active"
        item.started_at = now
        await session.commit()
        return {"session_id": str(item.id), "status": item.status}

# NATIVE_HTTP_GATEWAY_V1: authenticated device upload for an already-approved active session.
from fastapi import Depends as _NativeDepends, Request as _NativeRequest, HTTPException as _NativeHTTPException
from sqlalchemy import select as _native_select
from app.modules.devices.auth_dependency import get_authenticated_device as _native_device_auth
from app.modules.devices.auth_service import AuthenticatedDeviceContext as _NativeDeviceContext
from app.db.tenant import tenant_session as _native_tenant_session
from app.modules.live_monitoring.models import LiveScreenSession as _NativeSession
from app.modules.desktop_agent.models import DesktopAgentDevice
from app.modules.live_monitoring.native_http_gateway import publish as _native_publish
from app.modules.live_monitoring.native_frame_relay import RelayError as _NativeRelayError
from datetime import datetime as _NativeDateTime, timezone as _NativeTimezone

@router.post("/live-screen/{session_id}/native-frame")
async def native_frame_from_device(session_id: uuid.UUID, request: _NativeRequest,
        authenticated_device: _NativeDeviceContext = _NativeDepends(_native_device_auth)):
    if request.headers.get("content-type", "").split(";")[0].strip() != "image/jpeg":
        raise _NativeHTTPException(status_code=415, detail="JPEG only")
    if request.headers.get("content-length") and int(request.headers["content-length"]) > 900000:
        raise _NativeHTTPException(status_code=413, detail="Frame too large")
    data = bytearray()
    async for part in request.stream():
        data.extend(part)
        if len(data) > 900000:
            raise _NativeHTTPException(status_code=413, detail="Frame too large")
    async with _native_tenant_session(authenticated_device.database_name,
            cluster_key=authenticated_device.cluster_key) as tenant:
        native_desktop = await tenant.scalar(_native_select(DesktopAgentDevice).where(
            DesktopAgentDevice.installation_id == authenticated_device.device_uuid))
        item = await tenant.scalar(_native_select(_NativeSession).where(
            _NativeSession.id == session_id,
            _NativeSession.device_id == (native_desktop.id if native_desktop else uuid.UUID(int=0))))
        now = _NativeDateTime.now(_NativeTimezone.utc)
        if item is None or item.status != "active" or item.expires_at <= now or item.accepted_at is None:
            raise _NativeHTTPException(status_code=403, detail="Active employee-approved session required")
        ttl = max(1, int((item.expires_at - now).total_seconds()))
        try:
            seq = await _native_publish(str(authenticated_device.workspace_id), str(session_id),
                str(item.employee_id), str(item.device_id), ttl, bytes(data))
        except _NativeRelayError:
            raise _NativeHTTPException(status_code=422, detail="Invalid native frame")
        return {"sequence": seq}


