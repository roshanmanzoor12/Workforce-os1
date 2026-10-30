from __future__ import annotations
import ast
from datetime import datetime, timezone
from pathlib import Path
import shutil
import sys

ROOT = Path(r'C:\workforce-os')
TARGET = ROOT / 'backend/app/modules/website_tracking/agent_router.py'
OLD_IMPORT = '''from app.db.tenant import (
    tenant_session,
)'''
NEW_IMPORT = '''from sqlalchemy import select

from app.db.tenant import (
    tenant_session,
)
from app.modules.devices.models import Device'''
OLD_BLOCK = '''        return await coordinator.record_observation(
            device_id=(
                authenticated_device.device_id
            ),
            employee_id=None,
            request=payload,
        )'''
NEW_BLOCK = '''        # Resolve employee assignment from the authenticated tenant database.
        # Never trust a client-supplied employee identifier.
        assigned_employee_id = await session.scalar(
            select(Device.employee_id).where(
                Device.id == authenticated_device.device_id,
                Device.device_uuid == authenticated_device.device_uuid,
            )
        )

        return await coordinator.record_observation(
            device_id=(
                authenticated_device.device_id
            ),
            employee_id=assigned_employee_id,
            request=payload,
        )'''

def main() -> int:
    if not TARGET.is_file():
        print(f'ERROR: File missing: {TARGET}')
        return 1
    source = TARGET.read_text(encoding='utf-8-sig')
    if NEW_BLOCK in source and NEW_IMPORT in source:
        print('ALREADY PATCHED: no modifications made.')
        return 0
    if source.count(OLD_IMPORT) != 1 or source.count(OLD_BLOCK) != 1:
        print('ERROR: Unexpected website agent router layout; refusing to patch.')
        print(f'TARGET: {TARGET}')
        return 2
    updated = source.replace(OLD_IMPORT, NEW_IMPORT, 1).replace(OLD_BLOCK, NEW_BLOCK, 1)
    try:
        ast.parse(updated, filename=str(TARGET))
    except SyntaxError as exc:
        print(f'ERROR: Syntax check failed: {exc}')
        return 3
    backup = TARGET.with_name(TARGET.name + '.backup-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    shutil.copy2(TARGET, backup)
    try:
        TARGET.write_text(updated, encoding='utf-8')
    except Exception:
        shutil.copy2(backup, TARGET)
        raise
    print('PATCH APPLIED:', TARGET)
    print('BACKUP:', backup)
    print('PYTHON SYNTAX: PASS')
    print('NEXT: restart backend using its original environment; validate fresh records.')
    print('Historical rows are untouched. New unassigned devices remain unattributed.')
    return 0

if __name__ == '__main__':
    sys.exit(main())
