param([switch]$Apply,[switch]$Rollback)
$ErrorActionPreference = 'Stop'
$Root = 'C:\workforce-os'
$Web = Join-Path $Root 'apps\web'
$Files = @('app\(workspace)\monitoring\live-screen\page.tsx','components\monitoring\browser-screen-share-panel.tsx')
$Record = Join-Path $Root 'workforce-patch-backups\request-session-bridge-last-backup.txt'
if ($Rollback) {
 if (!(Test-Path -LiteralPath $Record)) { throw 'No backup record for this patch' }
 $Backup = (Get-Content -LiteralPath $Record -Raw).Trim()
 foreach ($Rel in $Files) {
  $Old=Join-Path $Backup $Rel; $Dst=Join-Path $Web $Rel
  if (!(Test-Path -LiteralPath $Old)) { throw "Backup missing $Old" }
  Copy-Item -LiteralPath $Old -Destination $Dst -Force
 }
 Write-Host 'ROLLBACK COMPLETE; restart frontend' -ForegroundColor Green
 exit 0
}
$CurrentPage=Join-Path $Web $Files[0]
$CurrentPanel=Join-Path $Web $Files[1]
if (!(Test-Path -LiteralPath $CurrentPage) -or !(Test-Path -LiteralPath $CurrentPanel)) { throw 'In-page browser sharing files absent' }
$PageText=Get-Content -LiteralPath $CurrentPage -Raw
if ($PageText -notmatch 'BrowserScreenSharePanel' -or $PageText -notmatch 'Open browser sharing here') { throw 'Unexpected Live Screen source; safe patch refused' }
if ($PageText -match 'browserRequestSignal') { throw 'Bridge already appears installed' }
foreach ($Rel in $Files) { if (!(Test-Path -LiteralPath (Join-Path (Join-Path $PSScriptRoot 'patch\apps\web') $Rel))) { throw "Patch missing $Rel" } }
Write-Host 'PREFLIGHT PASSED' -ForegroundColor Green
if (!$Apply) { Write-Host 'DRY RUN; pass -Apply to install'; exit 0 }
$Backup=Join-Path $Root ('workforce-patch-backups\request-session-bridge-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
foreach ($Rel in $Files) {
 $Dst=Join-Path $Web $Rel; $Back=Join-Path $Backup $Rel
 New-Item -ItemType Directory -Path (Split-Path $Back -Parent) -Force | Out-Null
 Copy-Item -LiteralPath $Dst -Destination $Back -Force
}
try {
 foreach ($Rel in $Files) {
  $Src=Join-Path (Join-Path $PSScriptRoot 'patch\apps\web') $Rel; $Dst=Join-Path $Web $Rel
  Copy-Item -LiteralPath $Src -Destination $Dst -Force
  if ((Get-FileHash -LiteralPath $Src -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $Dst -Algorithm SHA256).Hash) { throw "Verification failed: $Rel" }
  Write-Host "VERIFIED: $Rel" -ForegroundColor Green
 }
} catch {
 foreach ($Rel in $Files) { Copy-Item -LiteralPath (Join-Path $Backup $Rel) -Destination (Join-Path $Web $Rel) -Force }
 throw
}
Set-Content -LiteralPath $Record -Value $Backup
Write-Host "PATCH APPLIED. Backup: $Backup" -ForegroundColor Green
Write-Host 'Run npx tsc --noEmit --incremental false; restart frontend.'
