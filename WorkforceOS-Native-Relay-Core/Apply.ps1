param([switch]$Apply)
$ErrorActionPreference = 'Stop'
$Root = 'C:\workforce-os'
$Target = Join-Path $Root 'backend\app\modules\live_monitoring\native_frame_relay.py'
$Source = Join-Path $PSScriptRoot 'patch\backend\app\modules\live_monitoring\native_frame_relay.py'
if (!(Test-Path -LiteralPath $Source)) { throw "Patch file missing: $Source" }
if (!(Test-Path -LiteralPath (Split-Path $Target))) { throw 'Backend module folder missing' }
Write-Host 'Native relay core (NOT endpoint integration): preflight OK.' -ForegroundColor Green
if (!$Apply) { Write-Host 'Dry run only. -Apply to install standalone backend relay module.'; exit 0 }
$Backup = Join-Path $Root ('workforce-patch-backups\native-relay-core-' + (Get-Date -Format yyyyMMdd-HHmmss))
New-Item -ItemType Directory -Path $Backup -Force | Out-Null
if (Test-Path -LiteralPath $Target) { Copy-Item -LiteralPath $Target -Destination (Join-Path $Backup 'native_frame_relay.py') -Force }
Copy-Item -LiteralPath $Source -Destination $Target -Force
if ((Get-FileHash -LiteralPath $Source).Hash -ne (Get-FileHash -LiteralPath $Target).Hash) { throw 'Checksum mismatch' }
Write-Host "Installed backend core. Backup folder: $Backup" -ForegroundColor Green
Write-Host 'IMPORTANT: This is a standalone relay primitive. No API route or native streaming is enabled.' -ForegroundColor Yellow
