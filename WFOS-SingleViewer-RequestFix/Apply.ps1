param([switch]$Apply, [switch]$Rollback)
$ErrorActionPreference = 'Stop'
$Root = 'C:\workforce-os'
$Files = @('apps\web\app\(workspace)\monitoring\live-screen\page.tsx','apps\web\components\monitoring\browser-screen-share-panel.tsx')
$Bundle = Join-Path $PSScriptRoot 'patch'
$BackupRecord = Join-Path $PSScriptRoot 'last-backup.txt'
if ($Rollback) {
  if (!(Test-Path $BackupRecord)) { throw 'Backup pointer missing' }
  $Backup = (Get-Content $BackupRecord -Raw).Trim()
  foreach ($Rel in $Files) {
    $Src = Join-Path $Backup $Rel
    if (!(Test-Path -LiteralPath $Src)) { throw "Backup missing: $Src" }
    Copy-Item -LiteralPath $Src -Destination (Join-Path $Root $Rel) -Force
    Write-Host "RESTORED $Rel"
  }
  Write-Host 'ROLLBACK COMPLETE';exit 0
}
foreach ($Rel in $Files) {
 $Original = Join-Path $Root $Rel; $Replacement = Join-Path $Bundle $Rel
 if (!(Test-Path -LiteralPath $Original)) {throw "Project file missing: $Original"}
 if (!(Test-Path -LiteralPath $Replacement)) {throw "Patch file missing: $Replacement"}
}
$Page = Get-Content -LiteralPath (Join-Path $Root $Files[0]) -Raw
if ($Page -notmatch 'BrowserScreenSharePanel' -or $Page -notmatch 'browserRequestSignal') {throw 'Unexpected Live Screen version. No changes made.'}
if (!$Apply) {Write-Host 'DRY RUN PASSED. Rerun with -Apply.';exit 0}
$Backup = Join-Path $Root ('workforce-patch-backups\single-viewer-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
foreach ($Rel in $Files) {
 $Source = Join-Path $Root $Rel
 $Saved = Join-Path $Backup $Rel
 New-Item -Path (Split-Path $Saved -Parent) -ItemType Directory -Force | Out-Null
 Copy-Item -LiteralPath $Source -Destination $Saved -Force
}
$Backup | Set-Content -LiteralPath $BackupRecord
foreach ($Rel in $Files) {
 $Source = Join-Path $Bundle $Rel
 $Target = Join-Path $Root $Rel
 Copy-Item -LiteralPath $Source -Destination $Target -Force
 if ((Get-FileHash -LiteralPath $Source).Hash -ne (Get-FileHash -LiteralPath $Target).Hash) {throw "Copy verification failed: $Rel. Roll back with -Rollback."}
 Write-Host "VERIFIED $Rel" -ForegroundColor Green
}
Write-Host "PATCH APPLIED. Backup: $Backup" -ForegroundColor Green
Write-Host 'Run TypeScript validation and restart Next.js frontend only.'
