#!/usr/bin/env python3
"""Workforce OS: device-authenticated read-only live session inbox.
Does not authorize or initiate screen capture.
"""
from pathlib import Path
from datetime import datetime
import shutil, sys, py_compile

BLOCK = '''

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


class DeviceLiveInboxItem(BaseModel):
    session_id: uuid.UUID
    status: str
    expires_at: datetime
    consent_required: bool
    visible_indicator_required: bool


class DeviceLiveInboxResponse(BaseModel):
    sessions: list[DeviceLiveInboxItem]
    capture_authorized: bool = False


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
        result = await session.execute(
            select(LiveScreenSession)
            .where(LiveScreenSession.device_id == authenticated_device.device_id)
            .where(LiveScreenSession.status.in_(("requested", "accepted")))
            .where(LiveScreenSession.expires_at > datetime.now(timezone.utc))
            .order_by(LiveScreenSession.created_at.desc())
            .limit(20)
        )
        return DeviceLiveInboxResponse(
            sessions=[
                DeviceLiveInboxItem(
                    session_id=item.id,
                    status=item.status,
                    expires_at=item.expires_at,
                    consent_required=item.consent_required,
                    visible_indicator_required=item.visible_indicator_required,
                )
                for item in result.scalars().all()
            ],
            capture_authorized=False,
        )
'''

def main():
    root = Path(sys.argv[1] if len(sys.argv)>1 else r'C:\workforce-os')
    target = root / 'backend/app/modules/devices/agent_router.py'
    if not target.is_file():
        raise SystemExit(f'ERROR: Missing {target}')
    data = target.read_text(encoding='utf-8')
    if 'get_device_live_screen_inbox' in data:
        print('ALREADY INSTALLED', target)
        return
    if 'router = APIRouter(' not in data or 'AuthenticatedDevice' not in data:
        raise SystemExit('ERROR: Unexpected router structure; no changes made.')
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    backup = root / 'backups' / f'device-live-inbox-{stamp}' / 'backend/app/modules/devices/agent_router.py'
    backup.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(target, backup)
    # Existing module intentionally does not import uuid; appended route requires it.
    block = 'import uuid\n' + BLOCK
    target.write_text(data.rstrip()+'\n\n'+block,encoding='utf-8')
    try:
        py_compile.compile(str(target),doraise=True)
    except Exception:
        shutil.copy2(backup,target)
        raise
    print('PATCHED',target)
    print('BACKUP',backup)
    print('ENDPOINT GET /api/v1/device-agent/live-screen/inbox')
    print('IMPORTANT: Read-only device-scoped inbox; capture_authorized is always false.')
    print('IMPORTANT: No native capture, consent persistence or WebRTC transport installed.')

if __name__ == '__main__':
    main()
