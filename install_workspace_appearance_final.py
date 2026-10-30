#!/usr/bin/env python3
"""Back up and install the final, single-avatar workspace appearance page."""
from pathlib import Path
from datetime import datetime
import shutil, sys
root = Path(sys.argv[1] if len(sys.argv) > 1 else r'C:\workforce-os')
source = Path(__file__).with_name('workspace-appearance-final.tsx')
target = root / 'apps/web/app/(workspace)/settings/workspace/page.tsx'
if not source.is_file() or not target.is_file():
    raise SystemExit(f'Missing source or target: {source} / {target}')
text = source.read_text(encoding='utf-8')
for anchor in ('workspaceLogoSrc', 'api.postForm', 'workspacesService.update', 'Choose a company photo'):
    if anchor not in text: raise SystemExit(f'Invalid replacement: missing {anchor}')
backup = root / 'backups' / ('appearance-final-' + datetime.now().strftime('%Y%m%d-%H%M%S')) / 'page.tsx'
backup.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(target, backup)
target.write_text(text, encoding='utf-8')
print('INSTALLED:', target)
print('BACKUP:', backup)
print('NEXT: pnpm --dir apps/web exec tsc --noEmit')
