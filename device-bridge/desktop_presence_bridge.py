"""Synchronize desktop-monitoring presence from a credential-authenticated device.

The caller MUST have resolved device_id/device_uuid through the device authentication
headers and locked the corresponding tenant Device row. This module never accepts a
hostname, browser session, or employee-selected device ID as proof of identity.

A desktop record created here advertises NO screen-capture capabilities.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.desktop_agent.models import DesktopAgentDevice
from app.modules.employees.models import Employee
from app.modules.monitoring.models import MonitoringConsent
from app.modules.devices.models import Device


def _utc(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


async def synchronize_desktop_presence(
    session: AsyncSession,
    *,
    device: Device,
    seen_at: datetime,
) -> str:
    """Return a non-sensitive reconciliation outcome; caller owns the DB commit.

    Strong binding: desktop.installation_id = authenticated general.device_uuid.
    Ownership: assigned active employee must be linked to a user with saved consent.
    Do not silently transfer an installation between users or employees.
    """
    if not device.is_active or device.status in ("disabled", "revoked"):
        return "inactive"

    if device.employee_id is None:
        return "unassigned"

    employee = await session.scalar(
        select(Employee).where(
            Employee.id == device.employee_id,
            Employee.is_active.is_(True),
        )
    )
    if employee is None or employee.user_id is None:
        return "employee_unlinked"

    consent = await session.scalar(
        select(MonitoringConsent).where(
            MonitoringConsent.user_id == employee.user_id,
            MonitoringConsent.granted.is_(True),
            MonitoringConsent.revoked_at.is_(None),
        )
    )
    if consent is None:
        # No fresh desktop heartbeat if consent is off. The UI's freshness
        # window naturally expires; do not reactivate old enrollment.
        return "consent_missing"

    identity = device.device_uuid  # backend-issued, device-authenticated UUID
    existing = await session.scalar(
        select(DesktopAgentDevice)
        .where(DesktopAgentDevice.installation_id == identity)
        .with_for_update()
    )
    if existing is not None:
        if existing.user_id != employee.user_id or existing.employee_id != employee.id:
            return "ownership_conflict"
        if existing.is_disabled:
            return "disabled"
        existing.last_seen_at = _utc(seen_at)
        existing.status = "online"
        existing.device_name = device.hostname
        existing.agent_version = device.agent_version or existing.agent_version
        existing.os_version = device.os_version
        # A general heartbeat never asserts video readiness, even after an
        # older client may have written capabilities.
        existing.capabilities = {
            **(existing.capabilities or {}),
            "heartbeat": True,
            "live_screen": False,
            "screenshot_capture": False,
        }
        return "updated"

    session.add(DesktopAgentDevice(
        user_id=employee.user_id,
        employee_id=employee.id,
        installation_id=identity,
        device_name=device.hostname,
        platform="windows" if "windows" in device.os_name.lower() else "linux" if "linux" in device.os_name.lower() else "macos" if "mac" in device.os_name.lower() else "windows",
        os_version=device.os_version,
        agent_version=device.agent_version or "unknown",
        status="online",
        is_disabled=False,
        consent_version=consent.policy_version,
        consent_at=_utc(consent.granted_at or seen_at),
        capabilities={"heartbeat": True, "live_screen": False, "screenshot_capture": False},
        last_seen_at=_utc(seen_at),
        registered_at=_utc(seen_at),
    ))
    return "created"
