from __future__ import annotations
import argparse
from datetime import datetime
from pathlib import Path
import shutil
import sys

SIDEBAR = Path('apps/web/components/app-shell/app-sidebar.tsx')
APPEARANCE = Path('apps/web/app/(workspace)/settings/workspace/page.tsx')
OLD_BRAND = '''          className={styles.brandLink}
          style={mode === "workspace" ? { borderLeft: `3px solid ${workspace?.accent_color ?? "#F59E0B"}`, paddingLeft: 8 } : undefined}
        >
          <span
            className={styles.brandMark}
            aria-hidden="true"
            style={mode === "workspace" ? { backgroundColor: workspace?.primary_color ?? "#2563EB", color: "#FFFFFF", overflow: "hidden" } : undefined}
          >
            {mode === "workspace" && workspace?.logo_url ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={workspace.logo_url} alt="" style={{ width: "100%", height: "100%", objectFit: "cover" }} />
            ) : mode === "workspace" ? getInitials(currentWorkspaceName) : "W"}
          </span>'''
NEW_BRAND = '''          className={styles.brandLink}
        >
          <span
            className={styles.brandMark}
            aria-hidden="true"
          >
            W
          </span>'''


def main() -> int:
    p = argparse.ArgumentParser(description='Separate Workforce OS product branding from workspace branding.')
    p.add_argument('root', nargs='?', default=r'C:\workforce-os')
    args = p.parse_args()
    root = Path(args.root)
    targets = [root / SIDEBAR, root / APPEARANCE]
    for f in targets:
        if not f.is_file():
            raise RuntimeError(f'Missing required file (nothing changed): {f}')

    old_sidebar = targets[0].read_text(encoding='utf-8-sig')
    old_page = targets[1].read_text(encoding='utf-8-sig')
    if old_sidebar.count(OLD_BRAND) != 1:
        raise RuntimeError('Sidebar branding block differs from uploaded source; nothing changed. Export the latest sidebar.')
    if old_sidebar.count('primaryColor={workspaceRecord?.primary_color ?? "#2563EB"}') != 1:
        raise RuntimeError('Workspace picker marker not found; nothing changed.')
    # Validate both forms of the blue default in the appearance source before changing.
    required = [
        'useState("#2563EB")',
        'workspace?.primary_color ?? "#2563EB"',
    ]
    for marker in required:
        if old_page.count(marker) != 1:
            raise RuntimeError(f'Appearance marker differs: {marker}; nothing changed.')

    sidebar = old_sidebar.replace(OLD_BRAND, NEW_BRAND, 1)
    sidebar = sidebar.replace('primaryColor={workspaceRecord?.primary_color ?? "#2563EB"}', 'primaryColor={workspaceRecord?.primary_color ?? "#334155"}', 1)
    page = old_page.replace('useState("#2563EB")', 'useState("#334155")', 1)
    page = page.replace('workspace?.primary_color ?? "#2563EB"', 'workspace?.primary_color ?? "#334155"', 1)
    if sidebar == old_sidebar or page == old_page:
        raise RuntimeError('No changes generated; nothing changed.')

    backup = root / 'backups' / ('brand-separation-' + datetime.now().strftime('%Y%m%d-%H%M%S'))
    for rel in (SIDEBAR, APPEARANCE):
        (backup / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / rel, backup / rel)
    # Preserve existing line endings for source-control cleanliness.
    for f, original, updated in ((targets[0], old_sidebar, sidebar), (targets[1], old_page, page)):
        source_bytes = f.read_bytes()
        newline = '\r\n' if b'\r\n' in source_bytes else '\n'
        bom = b'\xef\xbb\xbf' if source_bytes.startswith(b'\xef\xbb\xbf') else b''
        temp = f.with_name(f.name + '.brand-separation-tmp')
        temp.write_bytes(bom + updated.replace('\n', newline).encode('utf-8'))
        temp.replace(f)
        print('UPDATED:', f)
    print('BACKUP:', backup)
    print('NOTE: already-saved blue workspace colors remain until you select/save a different color.')
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as exc:
        print('ERROR:', exc, file=sys.stderr)
        sys.exit(1)
