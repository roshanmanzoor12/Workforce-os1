
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import String, func, select

from app.db.tenant_dependency import TenantScope
from app.modules.activity.models import ActivityStateEvent
from app.modules.desktop_agent.models import DesktopAgentDevice
from app.modules.employees.models import Department, Employee
from app.modules.workspace_permissions.service import (
    WorkspacePermissionService,
)

from .models import (
    MonitoringConsent,
    MonitoringEvent,
    MonitoringLiveSession,
)

router = APIRouter(prefix="/workspaces", tags=["Monitoring"])

Section = Literal[
    "overview",
    "employees",
    "devices",
    "live-wall",
    "live-screen",
    "screenshots",
    "activity",
    "applications",
    "websites",
    "attendance",
    "alerts",
    "reports",
]

HEARTBEAT_FRESH_SECONDS = 120
ACTIVITY_FRESH_SECONDS = 120
INPUT_IDLE_SECONDS = 300


class ConsentRequest(BaseModel):
    granted: bool
    source: str = Field(default="native_agent", max_length=32)


class LiveSessionRequest(BaseModel):
    device_id: uuid.UUID


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def permissions(scope: TenantScope) -> WorkspacePermissionService:
    return WorkspacePermissionService(scope)


def require_read(scope: TenantScope) -> None:
    service = permissions(scope)

    if not any(
        service.has(key)
        for key in (
            "monitoring.all.read",
            "monitoring.team.read",
            "monitoring.self.read",
        )
    ):
        raise HTTPException(
            status_code=403,
            detail="Monitoring permission is required.",
        )


async def visible_employee_ids(
    scope: TenantScope,
) -> set[uuid.UUID] | None:
    """
    None means workspace-wide permission.
    Otherwise return only employee IDs within the
    authenticated actor's permitted monitoring scope.
    """
    service = permissions(scope)
    require_read(scope)

    if service.has("monitoring.all.read"):
        return None

    result = await scope.session.execute(
        select(Employee).where(
            Employee.user_id == scope.user_id,
            Employee.is_active.is_(True),
        )
    )
    actor = result.scalar_one_or_none()

    if actor is None:
        return set()

    if service.has("monitoring.team.read"):
        if actor.team_id is None:
            return {actor.id}

        rows = await scope.session.execute(
            select(Employee.id).where(
                Employee.team_id == actor.team_id,
                Employee.is_active.is_(True),
            )
        )
        return set(rows.scalars().all()) | {actor.id}

    if service.has("monitoring.self.read"):
        return {actor.id}

    return set()


def employee_filter(column, visible: set[uuid.UUID] | None):
    if visible is None:
        return None
    return column.in_(visible)


async def monitoring_snapshot(
    scope: TenantScope,
    section: str,
    search: str,
):
    """
    Build a monitoring snapshot from the existing
    tenant employee, agent and activity tables.

    Historical activity is never treated as live unless
    both the agent heartbeat and observation are fresh.
    """
    visible = await visible_employee_ids(scope)
    now = now_utc()

    heartbeat_cutoff = now - timedelta(
        seconds=HEARTBEAT_FRESH_SECONDS
    )
    activity_cutoff = now - timedelta(
        seconds=ACTIVITY_FRESH_SECONDS
    )

    employee_query = select(Employee).where(
        Employee.is_active.is_(True)
    )

    if visible is not None:
        employee_query = employee_query.where(
            Employee.id.in_(visible)
        )

    employee_query = employee_query.order_by(
        Employee.first_name, Employee.last_name
    )

    employees_result = await scope.session.execute(
        employee_query
    )
    employees = list(employees_result.scalars().all())

    employee_ids = {employee.id for employee in employees}

    departments = {}
    department_ids = {
        employee.department_id
        for employee in employees
        if employee.department_id is not None
    }

    if department_ids:
        department_result = await scope.session.execute(
            select(Department).where(
                Department.id.in_(department_ids)
            )
        )
        departments = {
            department.id: department.name
            for department in department_result.scalars().all()
        }

    devices = []
    if employee_ids:
        device_result = await scope.session.execute(
            select(DesktopAgentDevice).where(
                DesktopAgentDevice.employee_id.in_(employee_ids)
            ).order_by(
                DesktopAgentDevice.last_seen_at.desc().nullslast()
            )
        )
        devices = list(device_result.scalars().all())

    devices_by_employee = {}
    for device in devices:
        devices_by_employee.setdefault(
            device.employee_id, []
        ).append(device)

    device_ids = {device.id for device in devices}

    # The activity table references legacy devices.id,
    # not desktop_agent_devices.id in its foreign key.
    # Read only activity that has a trusted employee ID
    # and belongs to the visible employee scope.
    # Do not infer ownership from an unrelated device UUID.
    latest_activity_by_employee = {}

    if employee_ids:
        activity_result = await scope.session.execute(
            select(ActivityStateEvent)
            .where(
                ActivityStateEvent.employee_id.in_(employee_ids)
            )
            .order_by(
                ActivityStateEvent.observed_at.desc()
            )
            .limit(2000)
        )
        for event in activity_result.scalars().all():
            latest_activity_by_employee.setdefault(
                event.employee_id, event
            )

    employee_rows = []
    device_rows = []

    online_count = 0
    idle_count = 0
    offline_count = 0

    for employee in employees:
        owned_devices = devices_by_employee.get(
            employee.id, []
        )

        connected_devices = [
            device
            for device in owned_devices
            if (
                not device.is_disabled
                and device.status == "online"
                and device.last_seen_at is not None
                and device.last_seen_at >= heartbeat_cutoff
            )
        ]

        primary_device = (
            connected_devices[0]
            if connected_devices
            else (
                owned_devices[0]
                if owned_devices
                else None
            )
        )

        activity = latest_activity_by_employee.get(
            employee.id
        )

        fresh_activity = (
            activity is not None
            and activity.observed_at >= activity_cutoff
            and (
                activity.received_at is None
                or activity.received_at >= activity_cutoff
            )
            and bool(connected_devices)
            and activity.device_id in device_ids
        )

        # The legacy activity foreign key differs from the
        # desktop-agent table. If IDs don't match, preserve
        # history but do not assert live activity.
        if fresh_activity and activity.state == "idle":
            status = "idle"
            idle_count += 1
        elif connected_devices:
            status = "online"
            online_count += 1
        else:
            status = "offline"
            offline_count += 1

        full_name = " ".join(
            part
            for part in (
                employee.first_name,
                employee.last_name,
            )
            if part
        ).strip()

        employee_rows.append({
            "id": str(employee.id),
            "employee_id": str(employee.id),
            "employee": full_name,
            "name": full_name,
            "employee_code": employee.employee_code,
            "department": departments.get(
                employee.department_id, "Unassigned"
            ),
            "job_title": employee.job_title,
            "employment_status": employee.employment_status,
            "status": status,
            "device": (
                primary_device.device_name
                if primary_device
                else "No registered agent"
            ),
            "device_id": (
                str(primary_device.id)
                if primary_device
                else None
            ),
            "last_signal": (
                iso(primary_device.last_seen_at)
                if primary_device
                else None
            ),
            "last_activity": (
                iso(activity.observed_at)
                if activity
                else None
            ),
            "last_activity_state": (
                activity.state if activity else None
            ),
            "agent_ready": bool(connected_devices),
            "device_count": len(owned_devices),
        })

    for device in devices:
        fresh = (
            not device.is_disabled
            and device.status == "online"
            and device.last_seen_at is not None
            and device.last_seen_at >= heartbeat_cutoff
        )

        employee = next(
            (
                row
                for row in employee_rows
                if row["employee_id"] == str(device.employee_id)
            ),
            None,
        )

        device_rows.append({
            "id": str(device.id),
            "device_id": str(device.id),
            "employee_id": str(device.employee_id),
            "name": device.device_name,
            "device": device.device_name,
            "employee": employee["name"] if employee else "—",
            "platform": device.platform,
            "agent_version": device.agent_version,
            "status": (
                "disabled"
                if device.is_disabled
                else ("online" if fresh else "offline")
            ),
            "last_heartbeat": iso(device.last_seen_at),
            "last_seen_at": iso(device.last_seen_at),
            "agent_ready": fresh,
        })

    summary = {
        "employees": len(employees),
        "total_employees": len(employees),
        "online": online_count,
        "idle": idle_count,
        "offline": offline_count,
        "registered_devices": len(devices),
        "online_devices": sum(
            1 for row in device_rows
            if row["status"] == "online"
        ),
    }

    alerts = [
        {
            "id": f"unregistered-{row['employee_id']}",
            "employee_id": row["employee_id"],
            "employee": row["employee"],
            "title": "Monitoring agent not registered",
            "severity": "warning",
            "status": "open",
            "device": "No registered agent",
            "created_at": None,
            "source": "derived",
        }
        for row in employee_rows
        if row["device_count"] == 0
    ]

    alerts.extend(
        {
            "id": f"offline-{row['device_id']}",
            "employee_id": row["employee_id"],
            "employee": row["employee"],
            "title": "Monitoring device offline",
            "severity": "warning",
            "status": "open",
            "device": row["name"],
            "created_at": row["last_seen_at"],
            "source": "derived",
        }
        for row in device_rows
        if row["status"] == "offline"
    )

    if section in ("overview", "employees"):
        items = employee_rows
    elif section == "devices":
        items = device_rows
    elif section == "alerts":
        items = alerts
    elif section == "activity":
        activity_query = select(ActivityStateEvent).where(
            ActivityStateEvent.employee_id.in_(employee_ids)
        ).order_by(
            ActivityStateEvent.observed_at.desc()
        ).limit(100)

        result = await scope.session.execute(activity_query)

        items = [
            {
                "id": str(event.id),
                "employee_id": str(event.employee_id),
                "employee": next(
                    (
                        row["name"]
                        for row in employee_rows
                        if row["employee_id"]
                        == str(event.employee_id)
                    ),
                    "—",
                ),
                "device_id": str(event.device_id),
                "status": event.state,
                "idle_seconds": event.idle_seconds,
                "started_at": iso(event.observed_at),
                "captured_at": iso(event.observed_at),
                "last_input_at": iso(event.last_input_at),
                "source": "agent",
            }
            for event in result.scalars().all()
        ]
    else:
        items = []

    if search.strip():
        needle = search.strip().casefold()
        items = [
            row for row in items
            if any(
                needle in str(value).casefold()
                for value in row.values()
                if value is not None
            )
        ]

    return {
        "summary": summary,
        "items": items,
        "total": len(items),
        "generated_at": iso(now),
    }


# ============================================================
# CONSENT — SPECIFIC ROUTES BEFORE /{section}
# ============================================================


@router.get("/{workspace_id}/monitoring/consent")
async def get_consent(scope: TenantScope):
    require_read(scope)

    result = await scope.session.execute(
        select(MonitoringConsent).where(
            MonitoringConsent.user_id == scope.user_id
        )
    )
    consent = result.scalar_one_or_none()

    granted = bool(
        consent
        and consent.granted
        and consent.revoked_at is None
    )

    return {
        "required": not granted,
        "granted": granted,
        "policy_version": (
            consent.policy_version if consent else "v1"
        ),
    }


@router.post("/{workspace_id}/monitoring/consent")
async def save_consent(
    scope: TenantScope,
    payload: ConsentRequest,
):
    require_read(scope)

    result = await scope.session.execute(
        select(MonitoringConsent).where(
            MonitoringConsent.user_id == scope.user_id
        )
    )

    consent = result.scalar_one_or_none()
    now = now_utc()

    if consent is None:
        consent = MonitoringConsent(
            user_id=scope.user_id,
            granted=payload.granted,
            policy_version="v1",
            granted_at=now if payload.granted else None,
            revoked_at=now if not payload.granted else None,
        )
        scope.session.add(consent)
    else:
        consent.granted = payload.granted
        if payload.granted:
            consent.granted_at = now
            consent.revoked_at = None
        else:
            consent.revoked_at = now

    if not payload.granted:
        devices_result = await scope.session.execute(
            select(DesktopAgentDevice.id).where(
                DesktopAgentDevice.user_id == scope.user_id
            )
        )
        owned_ids = devices_result.scalars().all()

        if owned_ids:
            sessions = await scope.session.execute(
                select(MonitoringLiveSession).where(
                    MonitoringLiveSession.device_id.in_(owned_ids),
                    MonitoringLiveSession.status.in_(
                        ["requested", "accepted", "active"]
                    ),
                )
            )
            for session in sessions.scalars().all():
                session.status = "ended"
                session.ended_at = now
                session.end_reason = "consent_revoked"

    await scope.session.commit()

    return {
        "granted": consent.granted,
        "policy_version": consent.policy_version,
    }


# ============================================================
# LEGACY LIVE-SESSION ROUTES
# Prefer the existing /live-monitoring workflow for video.
# ============================================================


@router.post("/{workspace_id}/monitoring/live-sessions")
async def request_live_session(
    scope: TenantScope,
    payload: LiveSessionRequest,
):
    service = permissions(scope)
    service.require("monitoring.live_screen")

    if not service.has("monitoring.all.read"):
        raise HTTPException(
            status_code=403,
            detail="Workspace-wide access required.",
        )

    device = await scope.session.get(
        DesktopAgentDevice, payload.device_id
    )

    if device is None:
        raise HTTPException(
            status_code=404,
            detail="Monitoring device not found.",
        )

    if device.is_disabled:
        raise HTTPException(
            status_code=409,
            detail="Monitoring device is disabled.",
        )

    result = await scope.session.execute(
        select(MonitoringConsent).where(
            MonitoringConsent.user_id == device.user_id,
            MonitoringConsent.granted.is_(True),
            MonitoringConsent.revoked_at.is_(None),
        )
    )
    consent = result.scalar_one_or_none()

    if consent is None:
        raise HTTPException(
            status_code=403,
            detail="Device owner consent is required.",
        )

    session = MonitoringLiveSession(
        device_id=device.id,
        requested_by_user_id=scope.user_id,
        consent_id=consent.id,
        status="requested",
    )
    scope.session.add(session)

    await scope.session.commit()
    await scope.session.refresh(session)

    return {
        "session_id": str(session.id),
        "status": session.status,
    }


@router.post(
    "/{workspace_id}/monitoring/live-sessions/{session_id}/stop"
)
async def stop_live_session(
    scope: TenantScope,
    session_id: uuid.UUID,
):
    permissions(scope).require("monitoring.live_screen")

    session = await scope.session.get(
        MonitoringLiveSession, session_id
    )

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Live session not found.",
        )

    device = await scope.session.get(
        DesktopAgentDevice, session.device_id
    )

    if (
        session.requested_by_user_id != scope.user_id
        and (
            device is None
            or device.user_id != scope.user_id
        )
    ):
        raise HTTPException(
            status_code=403,
            detail="Cannot stop another user's session.",
        )

    if session.status != "ended":
        session.status = "ended"
        session.ended_at = now_utc()
        session.end_reason = "stopped_by_user"
        await scope.session.commit()

    return {
        "session_id": str(session.id),
        "status": session.status,
    }


# ============================================================
# SECTION API — REGISTER LAST
# ============================================================


@router.get("/{workspace_id}/monitoring/{section}")
async def monitoring_section(
    scope: TenantScope,
    section: Section,
    search: Annotated[str, Query(max_length=80)] = "",
):
    require_read(scope)

    if section in (
        "overview",
        "employees",
        "devices",
        "activity",
        "alerts",
    ):
        return await monitoring_snapshot(
            scope, section, search
        )

    visible = await visible_employee_ids(scope)

    # WFOS_DASHBOARD_USAGE_READ_V3: tenant-scoped employee-attributed usage.
    # Preserve visible_employee_ids authorization for all/team/self access.
    if section in ("applications", "websites"):
        from app.modules.app_tracking.models import AppUsageInterval
        from app.modules.website_tracking.models import WebsiteUsageInterval

        usage_model = (
            AppUsageInterval if section == "applications"
            else WebsiteUsageInterval
        )
        # Records without verified employee attribution must not be shown.
        conditions = [usage_model.employee_id.is_not(None)]
        if visible is not None:
            if not visible:
                return {
                    "summary": {"records": 0}, "items": [], "total": 0,
                    "generated_at": iso(now_utc()),
                }
            conditions.append(usage_model.employee_id.in_(visible))

        # Restrict to device/employee pair; avoid wrongly assigned historical
        # observations leaking into a different employee's dashboard.
        from app.modules.devices.models import Device
        conditions.extend([
            usage_model.device_id == Device.id,
            usage_model.employee_id == Device.employee_id,
        ])
        rows_result = await scope.session.execute(
            select(usage_model, Employee.first_name, Employee.last_name)
            .join(Device, usage_model.device_id == Device.id)
            .join(Employee, Employee.id == usage_model.employee_id)
            .where(*conditions)
            .order_by(usage_model.last_observed_at.desc())
            .limit(500)
        )
        items = []
        for usage, first_name, last_name in rows_result.all():
            employee_name = " ".join(
                str(piece) for piece in (first_name, last_name) if piece
            ).strip()
            item = {
                "id": str(usage.id),
                "employee_id": str(usage.employee_id),
                "device_id": str(usage.device_id),
                "employee": employee_name,
                "active_time": int(usage.duration_seconds or 0),
                "last_seen": iso(usage.last_observed_at),
                "captured_at": iso(usage.last_observed_at),
                "source": "agent",
            }
            if section == "applications":
                item["application"] = usage.process_name
            else:
                # Privacy: do not send URL, page title, or browser history.
                item["website"] = usage.normalized_domain
                item["category"] = "Uncategorized"
            if search.strip() and not any(
                search.strip().casefold() in str(value).casefold()
                for value in item.values() if value is not None
            ):
                continue
            items.append(item)
            if len(items) >= 100:
                break
        return {
            "summary": {"records": len(items)},
            "items": items,
            "total": len(items),
            "generated_at": iso(now_utc()),
        }

    filters = [MonitoringEvent.kind == section]

    # Unattributed events are deliberately excluded from
    # team/self monitoring responses.
    if visible is not None:
        filters.append(
            MonitoringEvent.employee_id.in_(visible)
        )

    if search.strip():
        filters.append(
            MonitoringEvent.payload.cast(String).ilike(
                f"%{search.strip()}%"
            )
        )

    total_result = await scope.session.execute(
        select(func.count(MonitoringEvent.id)).where(
            *filters
        )
    )

    rows_result = await scope.session.execute(
        select(MonitoringEvent)
        .where(*filters)
        .order_by(
            MonitoringEvent.captured_at.desc()
        )
        .limit(100)
    )

    items = [
        {
            **(row.payload or {}),
            "id": str(row.id),
            "employee_id": (
                str(row.employee_id)
                if row.employee_id else None
            ),
            "device_id": (
                str(row.device_id)
                if row.device_id else None
            ),
            "captured_at": iso(row.captured_at),
            "source": row.source,
        }
        for row in rows_result.scalars().all()
    ]


    total = int(total_result.scalar_one() or 0)

    return {
        "summary": {
            "records": total,
        },
        "items": items,
        "total": total,
        "generated_at": iso(now_utc()),
    }

