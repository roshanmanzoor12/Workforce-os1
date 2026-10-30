from pathlib import Path
import ast
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(r'C:\workforce-os')
apply = '--apply' in sys.argv[2:]
p = root / 'backend/app/modules/live_monitoring/native_frame_relay.py'
s = p.read_text(encoding='utf-8')
anchor = '            lease = _Lease(workspace_id, session_id, employee_id, device_id,\n                           time.monotonic() + expires_in)\n            self._leases[session_id] = lease'
replacement = '            lease = _Lease(workspace_id, session_id, employee_id, device_id,\n                           time.monotonic() + expires_in)\n            # Preserve the monotonic sequence across a media-ticket renewal.\n            # The browser sends ?after=<last sequence>; resetting to zero makes\n            # the browser discard every new frame until it catches up.\n            if existing is not None:\n                lease.sequence = existing.sequence\n            self._leases[session_id] = lease'
if replacement in s:
    print('ALREADY APPLIED: relay frame sequence continuity');sys.exit(0)
if s.count(anchor) != 1:
    raise SystemExit('PREFLIGHT FAILED: relay source differs from expected snapshot; nothing changed')
new = s.replace(anchor, replacement)
ast.parse(new, filename=str(p))
print('PREFLIGHT PASS: relay frame sequence continuity')
if not apply:
    print('DRY RUN ONLY; use -Apply installer flag.');sys.exit(0)
p.write_text(new,encoding='utf-8')
print('APPLIED:',p)
