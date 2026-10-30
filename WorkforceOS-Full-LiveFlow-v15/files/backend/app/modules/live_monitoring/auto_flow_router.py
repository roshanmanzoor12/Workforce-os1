"""Browser-authenticated employee login -> exactly one owner request per login/device.

Only the authenticated user can start/renew/end this browser work lease.
The owner is resolved from ACTIVE control-plane membership and its REAL RBAC.
A desktop device heartbeat alone NEVER constitutes an employee login.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_control_db
from app.modules.auth.permissions import authenticate_access_token
from app.modules.auth.models import RefreshSession
from app.modules.desktop_agent.models import DesktopAgentDevice
from app.modules.employees.models import Employee
from app.modules.live_monitoring.access import LiveMonitoringAccess
from app.modules.live_monitoring.login_lifecycle import LoginLiveScreenCoordinator, LoginLifecycleError
from app.modules.live_monitoring.models import LiveScreenSession
from app.modules.live_monitoring.native_http_gateway import revoke as revoke_frames
from app.modules.monitoring.models import MonitoringConsent
from app.modules.tenant_api.dependencies import get_authorized_tenant_context
from app.modules.workspace_permissions.permissions import WorkspacePermission
from app.modules.workspace_permissions.effective import resolve_membership_access
from app.modules.workspaces.models import (
    WorkspaceMembership, MEMBERSHIP_STATUS_ACTIVE, WORKSPACE_ROLE_OWNER,
)

router = APIRouter(prefix='/workspaces/{workspace_id}/live-monitoring', tags=['live-screen-auto-flow'])
Context = Annotated[Any, Depends(get_authorized_tenant_context)]
ControlDB = Annotated[AsyncSession, Depends(get_control_db)]
LEASE_SECONDS = 120

class SavedApprovalPayload(BaseModel):
    granted: bool


def utc_now():
    return datetime.now(timezone.utc)


def as_utc(dt):
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


async def verified_auth_session(request: Request, context: Any):
    """Check server-side refresh session, not JWT signature alone. Preserve root on rotations."""
    header = request.headers.get('authorization', '')
    if not header.lower().startswith('bearer '):
        raise HTTPException(401, 'Bearer session required')
    claims = authenticate_access_token(header[7:].strip())
    if claims.user_id != context.actor_user_id:
        raise HTTPException(403, 'Browser identity mismatch')
    control = context.control_session
    current = await control.get(RefreshSession, claims.session_id)
    now = utc_now()
    if (current is None or current.user_id != claims.user_id or current.revoked_at is not None or as_utc(current.expires_at) <= now):
        raise HTTPException(401, 'Browser session revoked or expired')
    # Refresh-token rotation can replace the server-side session ID. Resolve the
    # earliest session in the chain so token rotation does not cause new requests.
    root = current.id
    for _ in range(30):
        previous = await control.scalar(select(RefreshSession).where(
            RefreshSession.replaced_by_session_id == root,
            RefreshSession.user_id == claims.user_id,
        ))
        if previous is None:
            break
        root = previous.id
    else:
        raise HTTPException(409, 'Unexpected authentication rotation depth')
    return root


async def own_employee(context):
    employee = await context.tenant_session.scalar(select(Employee).where(
        Employee.user_id == context.actor_user_id, Employee.is_active.is_(True),
    ))
    return employee


async def owner_access(context, employee_id):
    # Never pretend that an employee/device is the owner. Verify owner membership
    # and its current control-plane RBAC, including employee-wide visibility.
    owners = (await context.control_session.execute(select(WorkspaceMembership).where(
        WorkspaceMembership.workspace_id == context.workspace_id,
        WorkspaceMembership.status == MEMBERSHIP_STATUS_ACTIVE,
        WorkspaceMembership.role_key == WORKSPACE_ROLE_OWNER,
    ).order_by(WorkspaceMembership.created_at.asc()))).scalars().all()
    for owner in owners:
        try:
            effective = await resolve_membership_access(
                context.control_session, workspace_id=context.workspace_id,
                membership=owner,
            )
        except Exception:
            # Banned, inactive or invalid memberships cannot authorize capture.
            continue
        permissions = effective.permissions
        if (WorkspacePermission.MONITORING_LIVE_SCREEN.value in permissions
                and WorkspacePermission.EMPLOYEES_ALL_READ.value in permissions):
            return LiveMonitoringAccess(
                workspace_id=context.workspace_id, actor_user_id=owner.user_id,
                actor_employee_id=None, visible_employee_ids=None,
                can_request_screenshot=WorkspacePermission.MONITORING_LIVE_VIEW.value in permissions,
                can_request_live_screen=True, can_manage_settings=False,
            )
    return None


async def revoke_sessions(context, login_id, employee_id, reason):
    tenant = context.tenant_session
    rows = (await tenant.execute(text('''
       UPDATE live_screen_login_lifecycle SET state='ended', ended_at=now()
       WHERE login_id=:login AND employee_id=:employee AND state <> 'ended'
       RETURNING live_session_id
    '''), {'login': login_id, 'employee': employee_id})).scalars().all()
    for sid in rows:
        item = await tenant.get(LiveScreenSession, sid)
        if item and item.employee_id == employee_id and item.status in ('requested', 'accepted', 'active'):
            item.status = 'ended'
            item.ended_at = utc_now()
            item.end_reason = reason
    await tenant.commit()
    for sid in rows:
        await revoke_frames(str(context.workspace_id), str(sid))
    return len(rows)


@router.post('/auto-flow/ping')
async def auto_flow_ping(workspace_id: uuid.UUID, request: Request, context: Context):
    login_id = await verified_auth_session(request, context)
    employee = await own_employee(context)
    if employee is None:
        return {'state': 'no_employee_profile'}
    tenant = context.tenant_session
    now = utc_now()
    desktop_devices = (await tenant.execute(select(DesktopAgentDevice).where(
        DesktopAgentDevice.user_id == context.actor_user_id,
        DesktopAgentDevice.employee_id == employee.id,
        DesktopAgentDevice.is_disabled.is_(False),
        DesktopAgentDevice.status == 'online',
        DesktopAgentDevice.last_seen_at > now - timedelta(seconds=90),
    ).order_by(DesktopAgentDevice.last_seen_at.desc()))).scalars().all()
    if not desktop_devices:
        return {'state': 'waiting_for_assigned_agent'}
    if len(desktop_devices) > 1:
        # Never choose an arbitrary device when a login has multiple eligible agents.
        return {'state': 'multiple_online_devices_require_selection'}
    desktop = desktop_devices[0]
    existing = (await tenant.execute(text('''
        SELECT state, live_session_id, owner_user_id FROM live_screen_login_lifecycle
        WHERE login_id=:login AND desktop_device_id=:device
    '''), {'login': login_id, 'device': desktop.id})).mappings().first()
    if existing:
        if existing['state'] == 'ended':
            return {'state': 'ended_for_this_login'}
        # Never continue streaming after the original owner loses permission.
        active_owner = await owner_access(context, employee.id)
        if active_owner is None or active_owner.actor_user_id != existing['owner_user_id']:
            await revoke_sessions(context, login_id, employee.id, 'owner_permission_revoked')
            return {'state': 'owner_permission_revoked'}
        screen = await tenant.get(LiveScreenSession, existing['live_session_id'])
        if screen is None or screen.status in ('denied', 'ended', 'expired'):
            await revoke_sessions(context, login_id, employee.id, 'session_terminal')
            return {'state': 'ended_for_this_login'}
        await tenant.execute(text('''
            UPDATE live_screen_login_lifecycle SET last_ping_at=now()
            WHERE login_id=:login AND desktop_device_id=:device AND state='requested'
        '''), {'login': login_id, 'device': desktop.id})
        # Keep a bounded media lease. Browser refresh preserves root login_id.
        if screen.status in ('accepted', 'active'):
            screen.expires_at = now + timedelta(seconds=LEASE_SECONDS)
        await tenant.commit()
        return {'state': screen.status, 'session_id': str(screen.id)}
    # A previous login or manual owner request may already hold the device.
    # Never attach a different browser login to that same live-screen session.
    preexisting = await tenant.scalar(select(LiveScreenSession).where(
        LiveScreenSession.device_id == desktop.id,
        LiveScreenSession.status.in_(('requested', 'accepted', 'active')),
        LiveScreenSession.expires_at > now,
    ).limit(1))
    if preexisting is not None:
        return {'state': 'existing_session_on_device'}
    # Owner is obtained from trusted control database and current RBAC.
    owner = await owner_access(context, employee.id)
    if owner is None:
        return {'state': 'no_authorized_owner'}
    try:
        sid = await LoginLiveScreenCoordinator(tenant).reconcile(
            login_id=login_id, employee_id=employee.id,
            desktop_device_id=desktop.id, owner_access=owner,
        )
    except LoginLifecycleError as exc:
        return {'state': 'not_ready', 'detail': str(exc)}
    except IntegrityError:
        # Concurrent browser logins may race for the same physical device.
        # Roll back instead of joining/reusing another login's authorization.
        await tenant.rollback()
        return {'state': 'existing_session_on_device'}
    await tenant.execute(text('''
        UPDATE live_screen_login_lifecycle SET last_ping_at=now()
        WHERE login_id=:login AND desktop_device_id=:device
    '''), {'login': login_id, 'device': desktop.id})
    await tenant.commit()
    return {'state': 'requested', 'session_id': str(sid)}


@router.post('/auto-flow/stop')
async def auto_flow_stop(workspace_id: uuid.UUID, request: Request, context: Context):
    login_id = await verified_auth_session(request, context)
    employee = await own_employee(context)
    if employee is None:
        return {'ended': 0}
    count = await revoke_sessions(context, login_id, employee.id, 'employee_logout_or_app_closed')
    return {'ended': count}


@router.get('/auto-flow/saved-approval')
async def get_saved_approval(workspace_id: uuid.UUID, context: Context):
    employee = await own_employee(context)
    if employee is None:
        return {'granted': False}
    row = (await context.tenant_session.execute(text('''
       SELECT granted FROM live_screen_saved_approvals
       WHERE user_id=:user AND employee_id=:employee AND revoked_at IS NULL
    '''), {'user': context.actor_user_id, 'employee': employee.id})).scalar_one_or_none()
    return {'granted': bool(row)}


@router.put('/auto-flow/saved-approval')
async def set_saved_approval(workspace_id: uuid.UUID, payload: SavedApprovalPayload, request: Request, context: Context):
    # This endpoint is invoked ONLY by an explicit user action in the workspace.
    # MonitoringConsent is deliberately not consulted or reused as screen approval.
    await verified_auth_session(request, context)
    employee = await own_employee(context)
    if employee is None:
        raise HTTPException(403, 'Active employee profile required')
    if payload.granted:
        monitoring = await context.tenant_session.scalar(select(MonitoringConsent.id).where(
            MonitoringConsent.user_id == context.actor_user_id,
            MonitoringConsent.granted.is_(True),
            MonitoringConsent.revoked_at.is_(None),
        ))
        if monitoring is None:
            raise HTTPException(403, 'Monitoring disclosure must be accepted before saving screen-specific approval')
    await context.tenant_session.execute(text('''
      INSERT INTO live_screen_saved_approvals
        (user_id, employee_id, granted, granted_at, revoked_at)
      VALUES (:user,:employee,:granted,now(),:revoked)
      ON CONFLICT (user_id,employee_id) DO UPDATE SET
        granted=EXCLUDED.granted, granted_at=EXCLUDED.granted_at,
        revoked_at=EXCLUDED.revoked_at
    '''), {'user': context.actor_user_id, 'employee': employee.id,
           'granted': payload.granted, 'revoked': None if payload.granted else utc_now()})
    await context.tenant_session.commit()
    if not payload.granted:
        # Revoking future approval ALSO ends currently auto-requested sharing.
        await context.tenant_session.execute(text('''
           UPDATE live_screen_login_lifecycle SET state='ended', ended_at=now()
           WHERE employee_id=:employee AND state <> 'ended'
        '''), {'employee': employee.id})
        items = (await context.tenant_session.execute(select(LiveScreenSession).where(
            LiveScreenSession.employee_id == employee.id,
            LiveScreenSession.status.in_(('requested','accepted','active')),
        ))).scalars().all()
        for item in items:
            item.status, item.ended_at, item.end_reason = 'ended', utc_now(), 'consent_revoked'
        await context.tenant_session.commit()
        for item in items:
            await revoke_frames(str(context.workspace_id), str(item.id))
    return {'granted': payload.granted}
