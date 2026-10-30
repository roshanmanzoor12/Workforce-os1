from __future__ import annotations

import ast
from datetime import datetime, timezone
from pathlib import Path
import shutil
import sys

ROOT = Path(r'C:\workforce-os')
TARGET = ROOT / 'backend' / 'app' / 'modules' / 'app_tracking' / 'agent_router.py'
OLD_IMPORT = 'from app.db.tenant import tenant_session'
NEW_IMPORT = 'from sqlalchemy import select\nfrom app.db.tenant import tenant_session\nfrom app.modules.devices.models import Device'
OLD_BLOCK = '''        coordinator = AppTrackingCoordinator(
            session
        )

        return await coordinator.record_observation(
            device_id=authenticated_device.device_id,
            device_uuid=authenticated_device.device_uuid,
            employee_id=None,
            payload=sanitized_payload,
        )'''
NEW_BLOCK = '''        # Resolve attribution from the authenticated tenant-local device.
        # Never accept employee identity from an Agent request payload.
        assigned_employee_id = await session.scalar(
            select(Device.employee_id).where(
                Device.id == authenticated_device.device_id,
                Device.device_uuid == authenticated_device.device_uuid,
            )
        )

        coordinator = AppTrackingCoordinator(
            session
        )

        return await coordinator.record_observation(
            device_id=authenticated_device.device_id,
            device_uuid=authenticated_device.device_uuid,
            employee_id=assigned_employee_id,
            payload=sanitized_payload,
        )'''

def main() -> int:
    if not TARGET.is_file():
        print(f'ERROR: Missing target file: {TARGET}')
        return 1
    original = TARGET.read_text(encoding='utf-8-sig')
    if NEW_BLOCK in original:
        print('ALREADY PATCHED: No changes made.')
        return 0
    if original.count(OLD_IMPORT) != 1 or original.count(OLD_BLOCK) != 1:
        print('ERROR: Source differs from expected structure. No changes made.')
        print('Check backend/app/modules/app_tracking/agent_router.py before patching.')
        return 2
    updated = original.replace(OLD_IMPORT, NEW_IMPORT, 1).replace(OLD_BLOCK, NEW_BLOCK, 1)
    try:
        ast.parse(updated, filename=str(TARGET))
    except SyntaxError as exc:
        print(f'ERROR: Patched source has invalid syntax: {exc}')
        return 3
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup = TARGET.with_name(f'{TARGET.name}.backup-{timestamp}')
    shutil.copy2(TARGET, backup)
    try:
        TARGET.write_text(updated, encoding='utf-8')
    except Exception:
        shutil.copy2(backup, TARGET)
        raise
    print(f'PATCH APPLIED: {TARGET}')
    print(f'BACKUP: {backup}')
    print('PYTHON SYNTAX: PASS')
    print('NEXT: restart FastAPI backend normally; then verify new app observations.')
    print('NOTE: historical rows are NOT updated.')
    return 0

if __name__ == '__main__':
    sys.exit(main())
