param([switch]$Apply,[switch]$Rollback)
$ErrorActionPreference = 'Stop'
$Root = 'C:\workforce-os'
$PatchRoot = Join-Path $PSScriptRoot 'patch\apps\web'
$Web = Join-Path $Root 'apps\web'
$Page = Join-Path $Web 'app\(workspace)\monitoring\live-screen\page.tsx'
$BrowserPage = Join-Path $Web 'app\(workspace)\browser-screen-share\page.tsx'
$Panel = Join-Path $Web 'components\monitoring\browser-screen-share-panel.tsx'
$Files = @(
  'app\(workspace)\monitoring\live-screen\page.tsx',
  'app\(workspace)\browser-screen-share\page.tsx',
  'components\monitoring\browser-screen-share-panel.tsx'
)
if ($Rollback) {
  $Record = Join-Path $Root 'workforce-patch-backups\inpage-livescreen-last-backup.txt'
  if (!(Test-Path $Record)) { throw 'No recorded backup for this patch.' }
  $Backup = (Get-Content -LiteralPath $Record -Raw).Trim()
  if (!(Test-Path $Backup)) { throw "Backup directory missing: $Backup" }
  foreach ($Relative in $Files) {
    $Old = Join-Path $Backup $Relative
    $Dest = Join-Path $Web $Relative
    if (Test-Path -LiteralPath $Old) { Copy-Item -LiteralPath $Old -Destination $Dest -Force }
    elseif (Test-Path -LiteralPath $Dest) { Remove-Item -LiteralPath $Dest -Force }
  }
  Write-Host 'Rollback completed. Restart frontend with the normal launcher.' -ForegroundColor Green
  exit 0
}
foreach($Relative in $Files) {
  $From = Join-Path $PatchRoot $Relative
  if (!(Test-Path -LiteralPath $From)) { throw "Patch file missing: $Relative" }
}
if (!(Test-Path -LiteralPath $Page) -or !(Test-Path -LiteralPath $BrowserPage)) { throw 'Target Live Screen or Browser Screen Share page missing.' }
$Current = Get-Content -LiteralPath $Page -Raw
if ($Current -notmatch 'Open Browser Screen Share') { throw 'Previous shortcut patch not detected; refuse to replace an unknown Live Screen page.' }
if ($Current -match 'BrowserScreenSharePanel') { throw 'In-page patch appears already installed. Do not apply twice.' }
Write-Host 'Preflight passed. Existing Live Screen shortcut found; browser page exists.' -ForegroundColor Green
if (!$Apply) { Write-Host 'DRY RUN ONLY. Rerun with -Apply to install.'; exit 0 }
$Backup = Join-Path $Root ('workforce-patch-backups\inpage-livescreen-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
foreach ($Relative in $Files) {
  $Dest = Join-Path $Web $Relative
  $Old = Join-Path $Backup $Relative
  if (Test-Path -LiteralPath $Dest) {
    New-Item -ItemType Directory -Path (Split-Path $Old -Parent) -Force | Out-Null
    Copy-Item -LiteralPath $Dest -Destination $Old -Force
  }
}
try {
  foreach ($Relative in $Files) {
    $From = Join-Path $PatchRoot $Relative
    $Dest = Join-Path $Web $Relative
    New-Item -ItemType Directory -Path (Split-Path $Dest -Parent) -Force | Out-Null
    Copy-Item -LiteralPath $From -Destination $Dest -Force
    $a = (Get-FileHash -LiteralPath $From -Algorithm SHA256).Hash
    $b = (Get-FileHash -LiteralPath $Dest -Algorithm SHA256).Hash
    if ($a -ne $b) { throw "Copy verification failed: $Relative" }
    Write-Host "VERIFIED: $Relative" -ForegroundColor Green
  }
} catch {
  foreach ($Relative in $Files) {
    $Old = Join-Path $Backup $Relative
    $Dest = Join-Path $Web $Relative
    if (Test-Path -LiteralPath $Old) { Copy-Item -LiteralPath $Old -Destination $Dest -Force }
    elseif (Test-Path -LiteralPath $Dest) { Remove-Item -LiteralPath $Dest -Force }
  }
  throw
}
$Record = Join-Path $Root 'workforce-patch-backups\inpage-livescreen-last-backup.txt'
Set-Content -LiteralPath $Record -Value $Backup
Write-Host "PATCH APPLIED. Backup: $Backup" -ForegroundColor Green
Write-Host 'Stop the frontend before rebuilding: dev/build share .next and can cause EPERM/ENOENT.' -ForegroundColor Yellow
