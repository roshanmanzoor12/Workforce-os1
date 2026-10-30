param([switch]$Apply,[switch]$Rollback)
$ErrorActionPreference = 'Stop'
$Root = 'C:\workforce-os'
$Files = @('apps\web\app\(workspace)\layout.tsx','apps\web\components\monitoring\browser-screen-share-panel.tsx','apps\web\components\monitoring\employee-screen-share-inbox.tsx')
$Bundle = Join-Path $PSScriptRoot 'patch'
$Pointer = Join-Path $PSScriptRoot 'last-backup.txt'
if ($Rollback) {
  if (!(Test-Path -LiteralPath $Pointer)) { throw 'Missing last-backup.txt' }
  $Backup=(Get-Content -LiteralPath $Pointer -Raw).Trim()
  foreach($Rel in $Files) {
    $Saved=Join-Path $Backup $Rel; $Target=Join-Path $Root $Rel
    if(Test-Path -LiteralPath $Saved) { Copy-Item -LiteralPath $Saved -Destination $Target -Force; Write-Host "RESTORED $Rel" }
    elseif ($Rel -like '*employee-screen-share-inbox.tsx') { Remove-Item -LiteralPath $Target -Force -ErrorAction SilentlyContinue; Write-Host "REMOVED $Rel" }
    else { throw "Required backup missing: $Saved" }
  }
  Write-Host 'ROLLBACK COMPLETE'; exit 0
}
foreach($Rel in $Files){if(!(Test-Path -LiteralPath (Join-Path $Bundle $Rel))){throw "Missing patch file: $Rel"}}
$Layout=Join-Path $Root $Files[0]
$Panel=Join-Path $Root $Files[1]
if(!(Test-Path -LiteralPath $Layout) -or !(Test-Path -LiteralPath $Panel)){throw 'Workspace layout or browser panel is missing'}
$LayoutText=Get-Content -LiteralPath $Layout -Raw
$PanelText=Get-Content -LiteralPath $Panel -Raw
if($LayoutText -notmatch 'MonitoringConsentGate' -or $PanelText -notmatch 'BrowserScreenSharePanel' -or $PanelText -notmatch 'requestSignal' -or $PanelText -match 'incomingOnly') {throw 'Unexpected project version. No change made.'}
if($LayoutText -match 'EmployeeScreenShareInbox') {throw 'Global inbox already installed. Refusing duplicate install.'}
if(!$Apply){Write-Host 'DRY RUN PASSED. Run -Apply to install.';exit 0}
$Backup=Join-Path $Root ('workforce-patch-backups\employee-screen-popup-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
foreach($Rel in $Files){$Original=Join-Path $Root $Rel;if(Test-Path -LiteralPath $Original){$Saved=Join-Path $Backup $Rel;New-Item -ItemType Directory -Force -Path (Split-Path $Saved -Parent)|Out-Null;Copy-Item -LiteralPath $Original -Destination $Saved -Force}}
$Backup | Set-Content -LiteralPath $Pointer
foreach($Rel in $Files){$From=Join-Path $Bundle $Rel;$To=Join-Path $Root $Rel;New-Item -ItemType Directory -Force -Path (Split-Path $To -Parent)|Out-Null;Copy-Item -LiteralPath $From -Destination $To -Force;if((Get-FileHash -LiteralPath $From).Hash -ne (Get-FileHash -LiteralPath $To).Hash){throw "Hash mismatch: $Rel"};Write-Host "VERIFIED: $Rel" -ForegroundColor Green}
Write-Host "PATCH APPLIED. Backup: $Backup" -ForegroundColor Green
Write-Host 'Run TypeScript and restart the frontend.'
