"""Local operator tool: bind the requested existing verified account to its UUID."""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path

from sqlalchemy import func, select

from app.config import settings
from app.core.database import ControlSessionLocal, control_engine
from app.modules.auth.models import User


def save_allowlist(env_file: Path, user_id: str):
    previous = env_file.read_bytes() if env_file.exists() else None
    body = previous.decode('utf-8-sig') if previous is not None else ''
    newline = '\r\n' if '\r\n' in body else '\n'
    values = {str(value) for value in settings.billing_unlimited_user_ids}
    matches = list(re.finditer(r'^BILLING_UNLIMITED_USER_IDS\s*=([^\r\n]*)', body, re.M))
    for match in matches:
        value = match[1].strip()
        if value.startswith("'") and value.endswith("'"):
            value = value[1:-1]
        stored = json.loads(value)
        if not isinstance(stored, list) or not all(isinstance(item, str) for item in stored):
            raise ValueError('Existing BILLING_UNLIMITED_USER_IDS must be a JSON array of UUID strings.')
        values.update(stored)
    values.add(user_id)
    line = 'BILLING_UNLIMITED_USER_IDS=' + json.dumps(sorted(values), separators=(',', ':'))
    if matches:
        updated = re.sub(r'^BILLING_UNLIMITED_USER_IDS\s*=[^\r\n]*', lambda _: line, body, flags=re.M)
    else:
        updated = body + (newline if body and not body.endswith('\n') else '') + line + newline
    if updated == body:
        print('Unlimited billing access is already configured for this verified user ID.')
        return
    # Fail before writing if a manually edited UUID is invalid.
    from uuid import UUID
    for value in values:
        UUID(value)
    if previous is not None:
        backup = env_file.with_name(env_file.name + '.unlimited-backup-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
        backup.write_bytes(previous)
    descriptor, temporary = tempfile.mkstemp(prefix='billing-access-', dir=env_file.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(updated.encode('utf-8'))
        if (env_file.read_bytes() if env_file.exists() else None) != previous:
            raise RuntimeError('The environment file changed during configuration. Run this command again.')
        os.replace(temporary, env_file)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    print('Unlimited billing access configured. Restart the backend to apply it.')


async def grant(email: str, project: Path):
    expected = Path(__file__).resolve().parents[4]
    if project.resolve() != expected:
        raise ValueError('Project root does not match the installed backend. No configuration was changed.')
    # Core columns avoid depending on unrelated ORM relationship registration.
    table = User.__table__
    async with ControlSessionLocal() as db:
        rows = list((await db.execute(select(
            table.c.id, table.c.is_active, table.c.is_email_verified, table.c.is_locked,
        ).where(func.lower(func.trim(table.c.email)) == email.strip().lower()))).mappings().all())
    if len(rows) != 1:
        raise ValueError('Exactly one existing account must match that email. No configuration was changed.')
    user = rows[0]
    if not user['is_active'] or not user['is_email_verified'] or user['is_locked']:
        raise ValueError('The account must be active, verified, and unlocked. No configuration was changed.')
    save_allowlist(project / '.env', str(user['id']))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--email', required=True)
    parser.add_argument('--project', required=True)
    args = parser.parse_args()
    async def run():
        try:
            await grant(args.email, Path(args.project))
        finally:
            await control_engine.dispose()
    asyncio.run(run())


if __name__ == '__main__':
    main()
