"""Persistent per-login live-screen request coordinator.

This module never treats an Agent heartbeat as browser login, and never derives
owner authority from device credentials. Callers must pass an owner-scoped
LiveMonitoringAccess independently resolved from a trusted, current identity.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.desktop_agent.models import DesktopAgentDevice
from app.modules.live_monitoring.access import LiveMonitoringAccess, can_access_employee
from app.modules.live_monitoring.schemas import LiveScreenRequestCreate
from app.modules.live_monitoring.service import LiveMonitoringService
from app.modules.live_monitoring.models import LiveScreenSession


class LoginLifecycleError(ValueError):
    pass


class LoginLiveScreenCoordinator:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def reconcile(self, *, login_id: uuid.UUID, employee_id: uuid.UUID,
                        desktop_device_id: uuid.UUID, owner_access: LiveMonitoringAccess):
        """Idempotently request once for a genuinely authenticated browser login.

        Caller MUST independently establish that login_id is an active auth
        session belonging to employee_id, and that owner_access was resolved
        for the authorized owner by the normal control-plane permission system.
        Requires the SQL migration included in this package.
        """
        if not owner_access.can_request_live_screen or not can_access_employee(
            access=owner_access, employee_id=employee_id
        ):
            raise LoginLifecycleError('Owner lacks employee-scoped live screen permission')
        device = await self.session.scalar(select(DesktopAgentDevice).where(
            DesktopAgentDevice.id == desktop_device_id,
            DesktopAgentDevice.employee_id == employee_id,
            DesktopAgentDevice.is_disabled.is_(False),
        ))
        if device is None or device.last_seen_at is None:
            raise LoginLifecycleError('Verified assigned desktop device required')
        seen = device.last_seen_at
        if seen.tzinfo is None:
            seen = seen.replace(tzinfo=timezone.utc)
        if (datetime.now(timezone.utc) - seen).total_seconds() > 90:
            raise LoginLifecycleError('Desktop device heartbeat is stale')

        # Protect even if duplicate concurrent callbacks land on separate workers.
        await self.session.execute(text('SELECT pg_advisory_xact_lock(hashtext(:key))'), {
            'key': f'workforce-live:{login_id}:{desktop_device_id}'
        })
        record = (await self.session.execute(text('''
            SELECT state, live_session_id FROM live_screen_login_lifecycle
            WHERE login_id=:login AND desktop_device_id=:device FOR UPDATE
        '''), {'login': login_id, 'device': desktop_device_id})).mappings().first()
        if record:
            # Existing declined, stopped, or ended login stays terminal; NEVER re-request.
            return record['live_session_id']

        # The requester is never synthesized from an untrusted device credential.
        response = await LiveMonitoringService(self.session).request_live_screen(
            access=owner_access,
            payload=LiveScreenRequestCreate(device_id=desktop_device_id, reason='Automatic work-session request'),
        )
        # request_live_screen() commits internally, so the lock above cannot be
        # relied on across that call. The unique constraint preserves this row;
        # the request service itself serializes per-device requests.
        await self.session.execute(text('''
            INSERT INTO live_screen_login_lifecycle
                (login_id, desktop_device_id, employee_id, owner_user_id, live_session_id, state)
            VALUES (:login,:device,:employee,:owner,:screen,'requested')
            ON CONFLICT (login_id,desktop_device_id) DO NOTHING
        '''), {'login': login_id, 'device': desktop_device_id, 'employee': employee_id,
               'owner': owner_access.actor_user_id, 'screen': response.id})
        await self.session.commit()
        return response.id

    async def revoke_login(self, *, login_id: uuid.UUID, employee_id: uuid.UUID,
                           reason: str = 'employee_logout') -> int:
        """Fail-closed server-side revocation for a verified employee login."""
        if reason not in {'employee_logout', 'app_closed', 'employee_stopped', 'consent_revoked'}:
            raise LoginLifecycleError('Unsupported revocation reason')
        rows = (await self.session.execute(text('''
            UPDATE live_screen_login_lifecycle SET state='ended', ended_at=now()
            WHERE login_id=:login AND employee_id=:employee AND state <> 'ended'
            RETURNING live_session_id
        '''), {'login': login_id, 'employee': employee_id})).scalars().all()
        if rows:
            await self.session.execute(text('''
                UPDATE live_screen_sessions SET status='ended', ended_at=now(), end_reason=:reason
                WHERE id = ANY(:ids) AND employee_id=:employee
                AND status IN ('requested','accepted','active')
            '''), {'ids': list(rows), 'employee': employee_id, 'reason': reason})
        await self.session.commit()
        return len(rows)
