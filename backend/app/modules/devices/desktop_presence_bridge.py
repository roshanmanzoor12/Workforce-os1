"""Synchronize desktop-monitoring presence from a credential-authenticated device.

The caller MUST have resolved device_id/device_uuid through the device authentication
headers and locked the corresponding tenant Device row. This module never accepts a
hostname, browser session, or employee-selected device ID as proof of identity.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.desktop_agent.models import DesktopAgentDevice
from app.modules.devices.models import Device
from app.modules.employees.models import Employee
from app.modules.monitoring.models import MonitoringConsent


def _utc(value: datetime) -> datetime:
    return (
        value
        if value.tzinfo
        else value.replace(tzinfo=timezone.utc)
    )


async def synchronize_desktop_presence(
    session: AsyncSession,
    *,
    device: Device,
    seen_at: datetime,
) -> str:
    """Synchronize the authenticated device heartbeat to desktop presence."""

    if not device.is_active or device.status in {
        "disabled",
        "revoked",
    }:
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
        return "consent_missing"

    identity = device.device_uuid

    existing = await session.scalar(
        select(DesktopAgentDevice)
        .where(
            DesktopAgentDevice.installation_id == identity,
        )
        .with_for_update()
    )

    if existing is not None:
        if (
            existing.user_id != employee.user_id
            or existing.employee_id != employee.id
        ):
            return "ownership_conflict"

        if existing.is_disabled:
            return "disabled"

        current_time = _utc(seen_at)

        existing.last_seen_at = current_time
        existing.updated_at = current_time
        existing.status = "online"
        existing.device_name = device.hostname
        existing.agent_version = (
            device.agent_version
            or existing.agent_version
        )
        existing.os_version = device.os_version

        existing.capabilities = {
            **(
                existing.capabilities
                or {}
            ),
            "heartbeat": True,
            "activity_state": True,
            "activity_reporting": True,
            "screen_capture": True,
            "live_screen": True,
            "screenshot_capture": False,
        }

        return "updated"

    current_time = _utc(seen_at)

    session.add(
        DesktopAgentDevice(
            user_id=employee.user_id,
            employee_id=employee.id,
            installation_id=identity,
            device_name=device.hostname,
            platform=(
                "windows"
                if "windows"
                in device.os_name.lower()
                else (
                    "linux"
                    if "linux"
                    in device.os_name.lower()
                    else (
                        "macos"
                        if "mac"
                        in device.os_name.lower()
                        else "windows"
                    )
                )
            ),
            os_version=device.os_version,
            agent_version=(
                device.agent_version
                or "unknown"
            ),
            status="online",
            is_disabled=False,
            consent_version=consent.policy_version,
            consent_at=_utc(
                consent.granted_at
                or seen_at
            ),
            capabilities={
                "heartbeat": True,
                "activity_state": True,
                "activity_reporting": True,
                "screen_capture": True,
                "live_screen": True,
                "screenshot_capture": False,
            },
            last_seen_at=current_time,
            updated_at=current_time,
            registered_at=current_time,
        )
    )

    return "created"