param([switch]$Apply)
$ErrorActionPreference = 'Stop'
$root='C:\workforce-os'
$stage=Join-Path $root 'artifacts\screen-companion-v9'
$live=Join-Path $root 'artifacts\screen-companion'
$dll='WorkforceOS.ScreenCompanion.dll'
if (!(Test-Path (Join-Path $stage $dll))) { throw 'v9 staging build missing.' }
if (!(Test-Path (Join-Path $live $dll))) { throw 'Live Companion path missing.' }
$before=(Get-FileHash (Join-Path $live $dll)).Hash
$expected=(Get-FileHash (Join-Path $stage $dll)).Hash
Write-Host "LIVE DLL: $before"
Write-Host "V9 DLL:   $expected"
$running=Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'WorkforceOS.ScreenCompanion.exe' }
$running | Select-Object ProcessId,ParentProcessId,CommandLine | Format-Table -AutoSize
if (!$Apply) { Write-Host 'PREFLIGHT PASS. Pause interactive Companion supervisor and ask employee to stop sharing first, then rerun -Apply.'; exit 0 }
if ($running) { throw 'Companion still running. Pause supervisor and stop sharing first; this installer will not kill the process or its parent.' }
$backup=Join-Path $root ('WorkforceOS-v9-companion-backup-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $backup | Out-Null
Copy-Item -Path (Join-Path $live '*') -Destination $backup -Recurse -Force -ErrorAction Stop
Write-Host "BACKUP: $backup"
try {
  Copy-Item -Path (Join-Path $stage '*') -Destination $live -Recurse -Force -ErrorAction Stop
  $actual=(Get-FileHash (Join-Path $live $dll)).Hash
  if ($actual -ne $expected) { throw 'DLL hash mismatch after copy' }
  Write-Host 'V9 COMPANION DEPLOYMENT VERIFIED: PASS' -ForegroundColor Green
  Write-Host 'Resume your existing interactive Companion supervisor. Restart backend via its existing launcher (new agent_router.py route).'
} catch {
  Write-Warning "Deploy failed; backup available at $backup. The supervisor must stay stopped until restored. Error: $_"
  throw
}
