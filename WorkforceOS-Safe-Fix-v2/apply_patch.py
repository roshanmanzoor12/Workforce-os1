#!/usr/bin/env python3
"""Fail-closed, bounded WorkforceOS backend fixes. No unverified C# edits."""
import argparse
import datetime
import pathlib
import re
import shutil
import sys

FILES = [
    'backend/app/modules/devices/heartbeat_service.py',
    'backend/app/modules/live_monitoring/service.py',
]

def patch_heartbeat(text):
    old = 'DEFAULT_HEARTBEAT_INTERVAL_SECONDS = 30'
    new = 'DEFAULT_HEARTBEAT_INTERVAL_SECONDS = 10'
    if text.count(old) == 1:
        return text.replace(old, new, 1)
    if text.count(new) == 1 and old not in text:
        return text
    raise ValueError('Unexpected heartbeat interval declaration; stop for review')

def patch_live_service(text):
    # Protect the request's existing 120-second approval deadline; extend only on verified activation.
    const = '    LIVE_ACTIVE_MAX_SECONDS = 900  # bounded employee-approved session, not request TTL\n'
    marker = '    LIVE_REQUEST_TTL_SECONDS = 120'
    if 'LIVE_ACTIVE_MAX_SECONDS = 900' not in text:
        if text.count(marker) != 1:
            raise ValueError('Could not uniquely locate LIVE_REQUEST_TTL_SECONDS')
        text = text.replace(marker, marker + '\n\n' + const.rstrip('\n'), 1)
    section = re.search(r'(?m)^    async def activate_live_screen\(.*?(?=^    async def |^__all__|\Z)', text, re.S | re.M)
    if not section:
        raise ValueError('activate_live_screen not found')
    start, end = section.span()
    s = section.group(0)
    if 'WFOS_ACTIVE_SESSION_EXPIRY_V2' in s:
        return text
    needle = re.compile(r'(?m)^(?P<indent>[ \t]*)item\.status\s*=\s*\(\s*LIVE_SESSION_STATUS_ACTIVE\s*\)', re.S)
    match = needle.search(s)
    if not match or len(list(needle.finditer(s))) != 1:
        raise ValueError('Unique activation assignment not found')
    # Both older formatted and current compact function use a prior `now = self._now()`.
    if not re.search(r'now\s*=\s*self\._now\(\)', s[:match.start()]):
        raise ValueError('Expected authoritative `now` before activation not found')
    insertion = ('        # WFOS_ACTIVE_SESSION_EXPIRY_V2\n'
                 '        # Approval-request TTL must not expire an already accepted session.\n'
                 '        # A bounded 15-minute lifetime still requires consent and explicit renewals.\n'
                 '        item.expires_at = now + timedelta(seconds=self.LIVE_ACTIVE_MAX_SECONDS)\n\n')
    s = s[:match.start()] + insertion + s[match.start():]
    return text[:start] + s + text[end:]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    root = pathlib.Path(args.root).resolve()
    if not root.is_dir():
        sys.exit('ERROR: Project root not found')
    patches = [patch_heartbeat, patch_live_service]
    changes=[]
    for rel, patcher in zip(FILES, patches):
        path = root/rel
        if not path.is_file():
            sys.exit(f'ERROR: Missing file {path}; no changes applied')
        raw = path.read_bytes()
        try:
            src=raw.decode('utf-8-sig')
            newline='\r\n' if b'\r\n' in raw else '\n'
            normalized=src.replace('\r\n','\n')
            updated=patcher(normalized)
            compile(updated, str(path), 'exec')
        except Exception as exc:
            sys.exit(f'ERROR: Preflight failed for {rel}: {exc}; no changes applied')
        encoded = (b'\xef\xbb\xbf' if raw.startswith(b'\xef\xbb\xbf') else b'') + updated.replace('\n',newline).encode('utf-8')
        changes.append((path, raw, encoded, rel))
    print('Preflight: PASS')
    for _, old, new, rel in changes:
        print(('CHANGED ' if old != new else 'ALREADY APPLIED ')+rel)
    if not args.apply:
        print('DRY RUN ONLY. Use -Apply with the PowerShell installer to update files.')
        return
    if all(old == new for _,old,new,_ in changes):
        print('Already applied: nothing to do.')
        return
    backup = root / ('WorkforceOS-Fix-v2-backup-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
    backup.mkdir(parents=True,exist_ok=False)
    try:
        for path, raw, new, rel in changes:
            dest=backup/rel
            dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_bytes(raw)
        for path, raw, new, rel in changes:
            if raw != new:
                path.write_bytes(new)
        print(f'Applied. Backup: {backup}')
    except Exception:
        for path, raw, new, rel in changes:
            path.write_bytes(raw)
        raise

if __name__ == '__main__':
    main()
