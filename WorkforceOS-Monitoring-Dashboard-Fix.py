#!/usr/bin/env python3
"""WorkforceOS dashboard read-model integration patch.
Run from C:\\workforce-os with .venv Python. Fail-closed source checks.
Only updates the monitoring_section endpoint; backs up original source.
"""
from __future__ import annotations
import ast
from datetime import datetime, timezone
from pathlib import Path
import py_compile
import re
import shutil
import sys

ROOT = Path(r'C:\workforce-os') if sys.platform == 'win32' else Path('/mnt/data')
TARGET = ROOT / 'backend/app/modules/monitoring/router.py'

REPLACEMENT = '''@router.get("/{workspace_id}/monitoring/{section}")
async def monitoring_section(scope: TenantScope, section: Section, search: Annotated[str, Query(max_length=80)] = ""):
    # Employee-level monitoring is sensitive. Do not reuse the broader
    # _can_read check for organization-wide device/activity results.
    from datetime import timedelta
    from sqlalchemy import or_
    from app.modules.devices.models import Device
    from app.modules.activity.models import ActivityStateEvent
    from app.modules.app_tracking.models import AppObservation, AppUsageInterval
    from app.modules.website_tracking.models import WebsiteObservation, WebsiteUsageInterval

    permission_service = WorkspacePermissionService(scope)
    live_sections = {"overview", "employees", "devices", "activity", "applications", "websites"}
    if section in live_sections:
        permission_service.require("monitoring.all.read")
    else:
        _can_read(scope)
        # Preserve existing dedicated sections; do not alter their behavior.
        query = (select(MonitoringEvent)
                 .where(MonitoringEvent.kind == section)
                 .order_by(MonitoringEvent.captured_at.desc())
                 .limit(100))
        rows = (await scope.session.execute(query)).scalars().all()
        term = search.strip().casefold()
        items = [
            {**(row.payload or {}), "id": str(row.id),
             "captured_at": row.captured_at.isoformat(), "source": row.source}
            for row in rows
        ]
        if term:
            items = [item for item in items if term in str(item).casefold()]
        return {"summary": {"records": len(items)}, "items": items,
                "total": len(items), "generated_at": datetime.now(timezone.utc).isoformat()}

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=24)
    online_cutoff = now - timedelta(minutes=2)
    term = search.strip().casefold()
    devices = (await scope.session.execute(
        select(Device).where(Device.is_active.is_(True),
                             Device.status.notin_(("revoked", "disabled")))
        .order_by(Device.last_seen_at.desc().nullslast()).limit(1000)
    )).scalars().all()
    device_by_id = {device.id: device for device in devices}

    def device_status(device):
        if device.last_seen_at is None or device.last_seen_at < online_cutoff:
            return "offline"
        return "online"

    def device_info(device):
        return {"device": device.hostname,
                "device_id": str(device.id),
                "employee": str(device.employee_id) if device.employee_id else "Unassigned"}

    def iso(value):
        return value.isoformat() if value is not None else None

    def matches(item):
        return not term or term in " ".join(str(v) for v in item.values() if v is not None).casefold()

    if section in ("overview", "devices", "employees"):
        items = []
        for device in devices:
            status = device_status(device)
            base = device_info(device)
            if section == "devices":
                item = {**base, "id": str(device.id), "name": device.hostname,
                        "platform": device.os_name, "status": status,
                        "last_heartbeat": iso(device.last_seen_at)}
            else:
                item = {**base, "id": str(device.id), "name": base["employee"],
                        "department": "—", "status": status,
                        "last_signal": iso(device.last_seen_at)}
            if matches(item):
                items.append(item)
        summary = {"devices": len(devices),
                   "online": sum(device_status(d) == "online" for d in devices),
                   "offline": sum(device_status(d) == "offline" for d in devices),
                   "assigned": sum(d.employee_id is not None for d in devices)}
        return {"summary": summary, "items": items[:100], "total": len(items),
                "generated_at": now.isoformat()}

    if section == "activity":
        records = (await scope.session.execute(
            select(ActivityStateEvent).where(ActivityStateEvent.observed_at >= cutoff)
            .order_by(ActivityStateEvent.observed_at.desc()).limit(300)
        )).scalars().all()
        items = []
        for record in records:
            device = device_by_id.get(record.device_id)
            if device is None:
                continue
            item = {"id": str(record.id), **device_info(device),
                    "started_at": iso(record.observed_at), "duration": record.idle_seconds,
                    "status": record.state}
            if matches(item): items.append(item)
    elif section == "applications":
        records = (await scope.session.execute(
            select(AppUsageInterval).where(AppUsageInterval.last_observed_at >= cutoff)
            .order_by(AppUsageInterval.last_observed_at.desc()).limit(300)
        )).scalars().all()
        items = []
        for record in records:
            device = device_by_id.get(record.device_id)
            if device is None: continue
            item = {"id": str(record.id), **device_info(device),
                    "application": record.process_name,
                    "active_time": record.duration_seconds,
                    "last_seen": iso(record.last_observed_at)}
            if matches(item): items.append(item)
    else:  # websites: domain only, no full URL or page title exposure
        records = (await scope.session.execute(
            select(WebsiteUsageInterval).where(WebsiteUsageInterval.last_observed_at >= cutoff)
            .order_by(WebsiteUsageInterval.last_observed_at.desc()).limit(300)
        )).scalars().all()
        items = []
        for record in records:
            device = device_by_id.get(record.device_id)
            if device is None: continue
            item = {"id": str(record.id), **device_info(device),
                    "website": record.normalized_domain,
                    "active_time": record.duration_seconds, "category": "—"}
            if matches(item): items.append(item)

    return {"summary": {"records_24h": len(items)}, "items": items[:100],
            "total": len(items), "generated_at": now.isoformat()}
'''

def main():
    if not TARGET.exists():
        raise RuntimeError(f'Missing router: {TARGET}')
    source = TARGET.read_text(encoding='utf-8')
    tree = ast.parse(source)
    funcs = [x for x in tree.body if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef)) and x.name == 'monitoring_section']
    if len(funcs) != 1:
        raise RuntimeError('Expected exactly one monitoring_section endpoint. No modifications.')
    node = funcs[0]
    section = '\n'.join(source.splitlines()[node.lineno-1:node.end_lineno])
    if 'device_status(device)' in section and 'WebsiteUsageInterval' in section:
        print('ALREADY APPLIED: no changes.')
        return
    for expected in ('MonitoringEvent.kind == section', '_can_read(scope)', 'row.payload', 'return {"summary"'):
        if expected not in section:
            raise RuntimeError('Unexpected router layout; refusing to replace live endpoint. Missing '+expected)
    decorator_start = min((d.lineno for d in node.decorator_list), default=node.lineno)
    lines = source.splitlines(keepends=True)
    replacement = REPLACEMENT.rstrip() + '\n'
    result = ''.join(lines[:decorator_start-1]) + replacement + ''.join(lines[node.end_lineno:])
    compile(result, str(TARGET), 'exec')
    backup = TARGET.with_name(TARGET.name + '.backup-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    shutil.copy2(TARGET, backup)
    try:
        TARGET.write_text(result, encoding='utf-8')
        py_compile.compile(str(TARGET), doraise=True)
    except Exception:
        shutil.copy2(backup, TARGET)
        raise
    print('PATCH APPLIED:', TARGET)
    print('BACKUP:', backup)
    print('PYTHON SYNTAX: PASS')
    print('NOTE: Organization-wide live monitoring requires monitoring.all.read.')
    print('NEXT: restart FastAPI and test with authorized Owner/Admin account.')

if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('ERROR:', exc, file=sys.stderr)
        sys.exit(1)
