#!/usr/bin/env python3
r"""Patch only monitoring applications/websites reads, preserving current permission scopes.

Usage Windows:
  .venv\Scripts\python.exe WorkforceOS-Monitoring-Dashboard-Current-Router-Fix.py
  .venv\Scripts\python.exe WorkforceOS-Monitoring-Dashboard-Current-Router-Fix.py --apply
"""
from __future__ import annotations
import argparse
import ast
from datetime import datetime, timezone
from pathlib import Path
import shutil
import sys

ROOT = Path(r'C:\workforce-os') if sys.platform == 'win32' else Path('/mnt/data')
TARGET = ROOT / 'backend/app/modules/monitoring/router.py'
MARKER = 'WFOS_DASHBOARD_USAGE_READ_V3'

BRANCH = '''    # WFOS_DASHBOARD_USAGE_READ_V3: tenant-scoped employee-attributed usage.
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

'''

def run(apply: bool) -> int:
    if not TARGET.is_file():
        raise RuntimeError(f"Missing router: {TARGET}")
    source = TARGET.read_text(encoding='utf-8-sig')
    tree = ast.parse(source, filename=str(TARGET))
    if MARKER in source:
        print('ALREADY PATCHED: marker found. No modifications.')
        return 0
    funcs = [n for n in tree.body if isinstance(n, ast.AsyncFunctionDef) and n.name == 'monitoring_section']
    if len(funcs) != 1:
        raise RuntimeError('Unexpected monitoring_section count; no modifications.')
    node = funcs[0]
    body_source = ast.get_source_segment(source, node) or ''
    required = (
        'require_read(scope)',
        'visible = await visible_employee_ids(scope)',
        'filters = [MonitoringEvent.kind == section]',
    )
    missing = [x for x in required if x not in body_source]
    if missing:
        raise RuntimeError('Unrecognized permission/section layout: ' + ', '.join(missing))
    if 'if section in (' not in body_source or 'return await monitoring_snapshot(' not in body_source:
        raise RuntimeError('Existing monitoring snapshot routing differs; no modifications.')
    # Insert immediately after the known current scope calculation.
    anchor = '    visible = await visible_employee_ids(scope)\n\n    filters = [MonitoringEvent.kind == section]'
    if source.count(anchor) != 1:
        raise RuntimeError('Insertion anchor not unique; no modifications.')
    updated = source.replace(anchor, '    visible = await visible_employee_ids(scope)\n\n' + BRANCH + '    filters = [MonitoringEvent.kind == section]', 1)
    compile(updated, str(TARGET), 'exec')
    print('SOURCE LAYOUT: PASS')
    print('PYTHON SYNTAX: PASS')
    print('PERMISSIONS: require_read + visible_employee_ids PRESERVED')
    print('SECTIONS CHANGED: applications, websites only')
    if not apply:
        print('DRY RUN ONLY. Use --apply after reviewing.')
        return 0
    backup = TARGET.with_name(TARGET.name + '.backup-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    if backup.exists():
        raise RuntimeError('Backup already exists. No changes.')
    shutil.copy2(TARGET, backup)
    try:
        TARGET.write_text(updated, encoding='utf-8')
        compile(TARGET.read_text(encoding='utf-8'), str(TARGET), 'exec')
    except Exception:
        shutil.copy2(backup, TARGET)
        raise
    print('PATCH APPLIED:', TARGET)
    print('BACKUP:', backup)
    print('Restart FastAPI normally, then test authorized /monitoring/applications and /monitoring/websites.')
    return 0

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    try:
        sys.exit(run(args.apply))
    except Exception as exc:
        print('SAFE STOP:', exc, file=sys.stderr)
        sys.exit(1)
