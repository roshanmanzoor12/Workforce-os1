"""DB-backed 120-second browser work lease checked before every native frame.
Manual owner-requested sessions remain under their existing authorization rules.
"""
from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import text, select
from app.modules.monitoring.models import MonitoringConsent
from app.modules.desktop_agent.models import DesktopAgentDevice
from app.modules.live_monitoring.models import LiveScreenSession
from app.modules.live_monitoring.native_http_gateway import revoke as revoke_frames


async def enforce_auto_lease(session, *, workspace_id, live_session_id) -> bool:
    result = (await session.execute(text('''
       SELECT state, last_ping_at FROM live_screen_login_lifecycle
       WHERE live_session_id=:sid LIMIT 1
    '''), {'sid': live_session_id})).mappings().first()
    if result is None:
        return True  # Manual sessions still use their normal approval checks.
    when = result['last_ping_at']
    current = await session.get(LiveScreenSession, live_session_id)
    desktop = (await session.get(DesktopAgentDevice, current.device_id)) if current else None
    monitored = bool(desktop and await session.scalar(select(MonitoringConsent.id).where(
        MonitoringConsent.user_id == desktop.user_id,
        MonitoringConsent.granted.is_(True),
        MonitoringConsent.revoked_at.is_(None),
    )))
    if (result['state'] != 'requested' or when is None or not monitored or
            (datetime.now(timezone.utc) - (
                when.replace(tzinfo=timezone.utc) if when.tzinfo is None else when
            )).total_seconds() > 120):
        await session.execute(text('''
           UPDATE live_screen_login_lifecycle SET state='ended', ended_at=now()
           WHERE live_session_id=:sid AND state <> 'ended'
        '''), {'sid': live_session_id})
        item = await session.get(LiveScreenSession, live_session_id)
        if item and item.status in ('requested', 'accepted', 'active'):
            item.status = 'ended'
            item.ended_at = datetime.now(timezone.utc)
            item.end_reason = 'browser_work_session_lease_expired'
        await session.commit()
        await revoke_frames(str(workspace_id), str(live_session_id))
        return False
    return True
