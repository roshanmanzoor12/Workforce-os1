from __future__ import annotations

import ast
from datetime import datetime, timezone
from pathlib import Path
import shutil
import sys

ROOT = Path(r'C:\workforce-os')
TARGET = ROOT / 'backend' / 'app' / 'modules' / 'website_tracking' / 'agent_router.py'
FUNCTION = 'report_device_website_observation'
LOOKUP_MARKER = 'assigned_employee_id = await session.scalar('


def fail(reason: str) -> int:
    print('ERROR:', reason)
    print('NO MODIFICATIONS MADE.')
    return 2


def main() -> int:
    if not TARGET.is_file():
        return fail(f'File not found: {TARGET}')
    original = TARGET.read_text(encoding='utf-8-sig')
    try:
        tree = ast.parse(original, filename=str(TARGET))
    except SyntaxError as exc:
        return fail(f'Existing source is invalid: {exc}')

    functions = [n for n in tree.body if isinstance(n, ast.AsyncFunctionDef) and n.name == FUNCTION]
    if len(functions) != 1:
        return fail('Expected exactly one website-observation endpoint.')
    fn = functions[0]
    calls = [n for n in ast.walk(fn) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == 'record_observation']
    if len(calls) != 1:
        return fail('Expected exactly one record_observation call in the endpoint.')
    call = calls[0]
    keywords = [k for k in call.keywords if k.arg == 'employee_id']
    if len(keywords) != 1:
        return fail('Expected exactly one employee_id argument.')
    keyword = keywords[0]

    if isinstance(keyword.value, ast.Name) and keyword.value.id == 'assigned_employee_id':
        if LOOKUP_MARKER in original:
            print('ALREADY PATCHED: employee lookup and call are present.')
            return 0
        return fail('Call references assigned_employee_id but lookup is missing.')
    if not (isinstance(keyword.value, ast.Constant) and keyword.value.value is None):
        return fail('Existing employee attribution is not None; refusing to overwrite customized code.')
    if LOOKUP_MARKER in original:
        return fail('Lookup already exists elsewhere; manual review required.')

    sessions = [n for n in ast.walk(fn) if isinstance(n, ast.AsyncWith) and any(isinstance(item.optional_vars, ast.Name) and item.optional_vars.id == 'session' for item in n.items)]
    if len(sessions) != 1:
        return fail('Expected exactly one async tenant session context.')
    block = sessions[0]
    if not any(isinstance(n, ast.Name) and n.id == 'authenticated_device' for n in ast.walk(block)):
        return fail('Expected authenticated-device context in tenant session.')
    if not any(isinstance(n, ast.Name) and n.id == 'coordinator' for n in ast.walk(block)):
        return fail('Expected coordinator in tenant session.')
    if not isinstance(block.body[0], ast.Assign):
        return fail('Unexpected first tenant-session statement; refusing automated insertion.')

    lines = original.splitlines(keepends=True)
    newline = '\r\n' if '\r\n' in original else '\n'
    # Replace only the AST-identified keyword-value token.
    value_line = keyword.value.lineno - 1
    start = keyword.value.col_offset
    end = keyword.value.end_col_offset
    line = lines[value_line]
    if line[start:end] != 'None':
        return fail('Employee argument token is not exactly None.')
    lines[value_line] = line[:start] + 'assigned_employee_id' + line[end:]

    indentation = ' ' * block.body[0].col_offset
    lookup = (
        f'{indentation}# Attribution comes only from the authenticated tenant-local device.\n'
        f'{indentation}assigned_employee_id = await session.scalar(\n'
        f'{indentation}    select(Device.employee_id).where(\n'
        f'{indentation}        Device.id == authenticated_device.device_id,\n'
        f'{indentation}        Device.device_uuid == authenticated_device.device_uuid,\n'
        f'{indentation}    )\n'
        f'{indentation})\n\n'
    ).replace('\n', newline)
    lines.insert(block.body[0].lineno - 1, lookup)
    updated = ''.join(lines)
    if 'from sqlalchemy import select' not in updated:
        anchor = 'from app.db.tenant import'
        if updated.count(anchor) != 1:
            return fail('Unable to safely place sqlalchemy.select import.')
        updated = updated.replace(anchor, f'from sqlalchemy import select{newline}{newline}' + anchor, 1)
    if 'from app.modules.devices.models import Device' not in updated:
        anchor = 'from app.modules.devices.auth_dependency import'
        if updated.count(anchor) != 1:
            return fail('Unable to safely place Device model import.')
        updated = updated.replace(anchor, f'from app.modules.devices.models import Device{newline}' + anchor, 1)

    try:
        new_tree = ast.parse(updated, filename=str(TARGET))
    except SyntaxError as exc:
        return fail(f'Patched source failed syntax validation: {exc}')
    new_fn = next(n for n in new_tree.body if isinstance(n, ast.AsyncFunctionDef) and n.name == FUNCTION)
    new_calls = [n for n in ast.walk(new_fn) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == 'record_observation']
    if len(new_calls) != 1 or not any(k.arg == 'employee_id' and isinstance(k.value, ast.Name) and k.value.id == 'assigned_employee_id' for k in new_calls[0].keywords):
        return fail('Post-patch attribution verification failed.')

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
    print('Restart existing backend, then verify fresh website observations.')
    print('Existing website records are unchanged.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
