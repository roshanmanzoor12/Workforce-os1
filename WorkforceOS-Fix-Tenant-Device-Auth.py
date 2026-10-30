"""Fail-closed tenant schema lineage validation for Workforce OS device auth.

Usage: C:\workforce-os\.venv\Scripts\python.exe WorkforceOS-Fix-Tenant-Device-Auth.py
"""
from __future__ import annotations
import ast
import datetime
from pathlib import Path
import shutil

ROOT = Path(r"C:\workforce-os")
TARGET = ROOT / 'backend/app/modules/devices/auth_service.py'
OLD_IMPORT = 'from dataclasses import dataclass\n'
NEW_IMPORT = ('from dataclasses import dataclass\n'
              'from pathlib import Path\n'
              '\nfrom alembic.script import ScriptDirectory\n'
              'from sqlalchemy import text\n')
OLD_CHECK = '''        if (
            metadata.schema_version
            != CURRENT_TENANT_SCHEMA_VERSION
        ):
            raise ResourceNotFound(
                "Device authentication failed."
            )'''
NEW_CHECK = '''        # Require a REAL applied Alembic revision at or beyond the
        # minimum supported revision; do not trust stale metadata alone.
        # A separate check confirms that metadata is an ancestor of the
        # database's recorded migration revision (no fabricated version).
        try:
            version_result = await tenant_db_session.execute(
                text("SELECT version_num FROM alembic_version")
            )
            applied = list(version_result.scalars().all())
            if len(applied) != 1:
                raise ValueError("Unexpected Alembic revision count")

            backend_dir = Path(__file__).resolve().parents[3]
            migrations_dir = backend_dir / "migrations" / "tenant"
            graph = ScriptDirectory(str(migrations_dir))
            database_revision = applied[0]
            if graph.get_revision(database_revision) is None:
                raise ValueError("Unknown applied Alembic revision")
            if graph.get_revision(CURRENT_TENANT_SCHEMA_VERSION) is None:
                raise ValueError("Unknown required Alembic revision")

            ancestors = {
                node.revision
                for node in graph.iterate_revisions(
                    database_revision, "base"
                )
            }
            if CURRENT_TENANT_SCHEMA_VERSION not in ancestors:
                raise ValueError("Required migration not applied")
            if metadata.schema_version not in ancestors:
                raise ValueError("Tenant metadata revision is not an ancestor")
        except Exception as exc:
            # Preserve generic error at the public authentication boundary.
            raise ResourceNotFound(
                "Device authentication failed."
            ) from exc'''

def main():
    if not TARGET.is_file():
        raise SystemExit(f'ERROR: Target not found: {TARGET}')
    original = TARGET.read_text(encoding='utf-8')
    if NEW_CHECK in original:
        print('ALREADY PATCHED (no modification)')
        return
    if original.count(OLD_CHECK) != 1 or original.count(OLD_IMPORT) != 1:
        raise SystemExit('ERROR: Unexpected auth_service.py version. No modification made.')
    patched = original.replace(OLD_IMPORT, NEW_IMPORT, 1).replace(OLD_CHECK, NEW_CHECK, 1)
    ast.parse(patched, filename=str(TARGET))
    backup = TARGET.with_name(TARGET.name + '.pre-schema-fix-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S') + '.bak')
    shutil.copy2(TARGET, backup)
    TARGET.write_text(patched, encoding='utf-8')
    print('PATCHED:', TARGET)
    print('BACKUP:', backup)
    print('Python AST syntax: PASS')
    print('No database/schema/credentials changed. Restart backend to apply.')
if __name__ == '__main__':
    main()
