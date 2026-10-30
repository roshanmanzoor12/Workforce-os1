#!/usr/bin/env python3
"""Bind website observations to the employee assigned to the authenticated device.

Source-safe patch: does not let device payload choose employee and does not enable
unannounced screen capture. Backs up the original file and supports --check.
"""
from pathlib import Path
from datetime import datetime
import argparse, shutil, sys

p = argparse.ArgumentParser()
p.add_argument('root', nargs='?', default=r'C:\workforce-os')
p.add_argument('--check', action='store_true')
a = p.parse_args()
target = Path(a.root) / 'backend/app/modules/website_tracking/agent_router.py'
if not target.is_file():
    sys.exit(f'MISSING: {target}')
src = target.read_text(encoding='utf-8')
old_import = '''from fastapi import (
    APIRouter,
    Depends,
    status,
)
'''
new_import = old_import + '''from sqlalchemy import select

from app.modules.devices.models import Device
'''
old_call = '''        return await coordinator.record_observation(
            device_id=(
                authenticated_device.device_id
            ),
            employee_id=None,
            request=payload,
        )'''
new_call = '''        # Resolve the employee from the authenticated tenant-local device.
        # Never accept employee identity from a client-supplied observation.
        employee_id = await session.scalar(
            select(Device.employee_id).where(
                Device.id == authenticated_device.device_id
            )
        )

        return await coordinator.record_observation(
            device_id=(
                authenticated_device.device_id
            ),
            employee_id=employee_id,
            request=payload,
        )'''
if 'employee_id = await session.scalar(' in src and 'from app.modules.devices.models import Device' in src:
    print('ALREADY PATCHED:', target)
    sys.exit(0)
if src.count(old_import)!=1 or src.count(old_call)!=1:
    sys.exit('ABORT: source format differs. No files modified. Please export current agent_router.py.')
patched = src.replace(old_import, new_import, 1).replace(old_call,new_call,1)
compile(patched, str(target), 'exec')
if a.check:
    print('CHECK PASSED: patch applies cleanly; no files modified')
    sys.exit(0)
backup = Path(a.root) / 'backups' / ('agent-employee-website-'+datetime.now().strftime('%Y%m%d-%H%M%S')) / 'backend/app/modules/website_tracking/agent_router.py'
backup.parent.mkdir(parents=True,exist_ok=True)
shutil.copy2(target, backup)
target.write_text(patched, encoding='utf-8')
print('PATCHED',target)
print('BACKUP',backup)
print('NOTE: URL/domain attribution only; existing privacy policy still suppresses full URL and title.')
print('NOTE: This does not implement live video, consent persistence, or C# agent streaming.')
