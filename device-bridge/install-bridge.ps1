$ErrorActionPreference = 'Stop'
$Root = 'C:\workforce-os'
$SourceDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Target = Join-Path $Root 'backend\app\modules\devices\desktop_presence_bridge.py'
$Heartbeat = Join-Path $Root 'backend\app\modules\devices\heartbeat_service.py'
$Source = Join-Path $SourceDir 'desktop_presence_bridge.py'
if (!(Test-Path $Source)) { throw 'Put both downloaded files in the same folder.' }
if (!(Test-Path $Heartbeat)) { throw "Missing: $Heartbeat" }
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$backup = "$Heartbeat.backup-$stamp"
Copy-Item $Heartbeat $backup
if (Test-Path $Target) { Copy-Item $Target "$Target.backup-$stamp" }
@'
from pathlib import Path
import ast, sys
p = Path(sys.argv[1])
s = p.read_text(encoding='utf-8-sig')
marker = 'WFOS_AUTHENTICATED_DESKTOP_PRESENCE_V1'
if marker in s:
    print('Heartbeat bridge already installed')
    raise SystemExit(0)
anchor_import = 'from app.modules.devices.models import ('
if s.count(anchor_import) != 1:
    raise SystemExit('Expected devices.models import anchor not found; no changes')
s = s.replace(anchor_import, 'from app.modules.devices.desktop_presence_bridge import synchronize_desktop_presence\n' + anchor_import, 1)
# Call while the authenticated Device record is locked, before existing commit.
method_start = s.index('    async def record_heartbeat(')
method = s[method_start:]
anchor_commit = '        try:\n            await self.session.commit()'
if method.count(anchor_commit) != 1:
    raise SystemExit('Heartbeat commit anchor not unique; no changes')
sync = '''        # WFOS_AUTHENTICATED_DESKTOP_PRESENCE_V1
        # Device is resolved by X-Device-UUID / X-Device-Secret above.
        # Sync does not grant screen-capture capability.
        await synchronize_desktop_presence(
            self.session,
            device=device,
            seen_at=now,
        )

'''
method = method.replace(anchor_commit, sync + anchor_commit, 1)
s = s[:method_start] + method
ast.parse(s, filename=str(p))
p.write_text(s, encoding='utf-8')
print('Authenticated desktop heartbeat bridge installed')
'@ | Set-Content -LiteralPath (Join-Path $env:TEMP 'wfos-patch-bridge.py') -Encoding UTF8
try {
  Copy-Item $Source $Target -Force
  python (Join-Path $env:TEMP 'wfos-patch-bridge.py') $Heartbeat
  if ($LASTEXITCODE -ne 0) { throw 'Source patch failed' }
  python -m py_compile $Heartbeat $Target
  if ($LASTEXITCODE -ne 0) { throw 'Syntax check failed' }
  Write-Host 'BRIDGE INSTALLED - Python syntax PASS' -ForegroundColor Green
  Write-Host "Backup: $backup"
} catch {
  Copy-Item $backup $Heartbeat -Force
  if (Test-Path "$Target.backup-$stamp") { Copy-Item "$Target.backup-$stamp" $Target -Force }
  else { Remove-Item $Target -ErrorAction SilentlyContinue }
  throw
}
