param([switch]$Apply, [string]$Root = 'C:\workforce-os')
$ErrorActionPreference = 'Stop'
$Python = Join-Path $Root '.venv\Scripts\python.exe'
if (!(Test-Path $Python)) { $Python = 'python' }
$Patcher = Join-Path $PSScriptRoot 'patch_sources.py'
if (!(Test-Path $Patcher)) { throw 'V15 patcher file is missing' }
if ($Apply) {
  & $Python $Patcher --root $Root --apply
} else {
  & $Python $Patcher --root $Root
}
if ($LASTEXITCODE -ne 0) { throw "V15 preflight/apply FAILED (exit $LASTEXITCODE). See SOURCE CONFLICT above." }
if (!$Apply) { Write-Host 'PREFLIGHT ONLY: No live changes.' -ForegroundColor Green }
else {
  Write-Host 'V15 SOURCE PATCHED: check tenant migrations and compile backend/frontend/Agent/Companion before any service deployment.' -ForegroundColor Yellow
  Write-Host 'No service was restarted and no database migration was executed.'
}
