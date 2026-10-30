param([switch]$Apply)
$ErrorActionPreference = 'Stop'
$Root = 'C:\workforce-os'
$P = Join-Path $Root 'backend\app\modules\live_monitoring\service.py'
$L = Join-Path $Root 'backend\app\modules\live_monitoring\login_lifecycle.py'
if (!(Test-Path $P) -or !(Test-Path $L)) { throw 'Missing service.py or staged v11 login_lifecycle.py' }
$s = [IO.File]::ReadAllText($P)
$l = [IO.File]::ReadAllText($L)
$head = $s.IndexOf('    async def request_live_screen(')
$tail = $s.IndexOf('    async def decide_live_screen(', $head)
if ($head -lt 0 -or $tail -lt 0) { throw 'Unexpected live-screen method layout. NO CHANGES.' }
$block = $s.Substring($head,$tail-$head)
if ($block.Contains('        commit: bool = True,') -and $l.Contains('            commit=False,')) { Write-Host 'V12 ALREADY APPLIED'; exit 0 }
$needle = "        payload: LiveScreenRequestCreate,`n    ) -> LiveScreenResponse:"
$oldCommit = "        # Commit the request before returning so the separate native agent`n        # heartbeat/inbox connection can see and deliver the popup.`n        await self.session.commit()`n        await self.session.refresh(item)"
$oldCall = "            payload=LiveScreenRequestCreate(device_id=desktop_device_id, reason='Automatic work-session request'),`n        )"
$oldNote = "        # request_live_screen() commits internally, so the lock above cannot be`n        # relied on across that call. The unique constraint preserves this row;`n        # the request service itself serializes per-device requests."
# Normalize CRLF for safe exact block replacement; restore line-ending style at write.
$crlfS = $s.Contains("`r`n")
$crlfL = $l.Contains("`r`n")
$s = $s.Replace("`r`n","`n"); $l = $l.Replace("`r`n","`n")
$head = $s.IndexOf('    async def request_live_screen(')
$tail = $s.IndexOf('    async def decide_live_screen(', $head)
$block = $s.Substring($head,$tail-$head)
if (!$block.Contains($needle) -or !$block.Contains($oldCommit) -or !$l.Contains($oldCall) -or !$l.Contains($oldNote)) {throw 'SOURCE CONFLICT: Expected V11 baseline not found. No changes made.'}
if (($block.Split([string[]]@('        await self.session.commit()'),[StringSplitOptions]::None)).Count -ne 2) {throw 'Unexpected commit count. No changes made.'}
$newBlock = $block.Replace($needle,"        payload: LiveScreenRequestCreate,`n        commit: bool = True,`n    ) -> LiveScreenResponse:")
$newBlock = $newBlock.Replace($oldCommit,"        # Manual requests commit now; coordinator commits request and mapping together.`n        if commit:`n            await self.session.commit()`n        else:`n            await self.session.flush()`n        await self.session.refresh(item)")
$s2 = $s.Substring(0,$head) + $newBlock + $s.Substring($tail)
$l2 = $l.Replace($oldCall,"            payload=LiveScreenRequestCreate(device_id=desktop_device_id, reason='Automatic work-session request'),`n            commit=False,`n        )")
$l2 = $l2.Replace($oldNote,'        # Request and lifecycle mapping commit together under the same DB lock.')
Write-Host 'PREFLIGHT PASS: atomic request + lifecycle mapping'
if (!$Apply) {Write-Host 'DRY RUN ONLY. Use -Apply.'; exit 0}
$backup = Join-Path $Root ('WorkforceOS-v12-backup-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $backup -Force | Out-Null
Copy-Item $P (Join-Path $backup 'service.py') -ErrorAction Stop
Copy-Item $L (Join-Path $backup 'login_lifecycle.py') -ErrorAction Stop
if ($crlfS) {$s2=$s2.Replace("`n","`r`n")}
if ($crlfL) {$l2=$l2.Replace("`n","`r`n")}
[IO.File]::WriteAllText($P,$s2,[Text.UTF8Encoding]::new($false))
[IO.File]::WriteAllText($L,$l2,[Text.UTF8Encoding]::new($false))
& python -m py_compile $P $L
if ($LASTEXITCODE -ne 0) {Copy-Item (Join-Path $backup 'service.py') $P -Force; Copy-Item (Join-Path $backup 'login_lifecycle.py') $L -Force; throw 'Syntax check failed. Backups restored.'}
Write-Host 'V12 SOURCE PATCH VERIFIED. Backend NOT restarted. Migration NOT applied.' -ForegroundColor Green
Write-Host "Backup: $backup"
