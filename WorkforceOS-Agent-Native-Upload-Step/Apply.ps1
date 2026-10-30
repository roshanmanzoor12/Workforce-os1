param([switch]$Apply, [switch]$Rollback)
$ErrorActionPreference = 'Stop'
$Root = 'C:\workforce-os'
$Relative = 'agent\WorkforceOS.Agent\LiveScreen\NativeFrameUploadClient.cs'
$Destination = Join-Path $Root $Relative
$Source = Join-Path $PSScriptRoot ('patch\' + $Relative)
$BackupBase = Join-Path $Root 'workforce-patch-backups'
$Marker = Join-Path $PSScriptRoot '.latest-backup.txt'
if (!(Test-Path -LiteralPath $Source)) { throw 'Patch source missing' }
if (!(Test-Path -LiteralPath (Split-Path $Destination))) { throw 'Agent LiveScreen folder missing' }
if ($Rollback) {
  if (!(Test-Path -LiteralPath $Marker)) { throw 'No installation marker: cannot choose safe rollback' }
  $Backup = Get-Content -LiteralPath $Marker -Raw
  $Backup = $Backup.Trim()
  $PreviouslyPresent = Join-Path $Backup 'previous-present.txt'
  if (Test-Path -LiteralPath $PreviouslyPresent) {
    Copy-Item -LiteralPath (Join-Path $Backup 'NativeFrameUploadClient.cs') -Destination $Destination -Force
  } else { Remove-Item -LiteralPath $Destination -ErrorAction SilentlyContinue }
  Write-Host "Rollback complete using $Backup"; exit 0
}
if (Test-Path -LiteralPath $Destination) {
  $OldHash = (Get-FileHash -LiteralPath $Destination -Algorithm SHA256).Hash
  $NewHash = (Get-FileHash -LiteralPath $Source -Algorithm SHA256).Hash
  if ($OldHash -ne $NewHash) { throw "Existing NativeFrameUploadClient.cs differs. Refusing overwrite. $Destination" }
  Write-Host 'Already installed: same hash. No changes needed.'; exit 0
}
if (!$Apply) { Write-Host 'DRY RUN PASSED. Adds one Agent source file only. Does not activate streaming.'; exit 0 }
$Backup = Join-Path $BackupBase ('native-upload-step-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $Backup -Force | Out-Null
Copy-Item -LiteralPath $Source -Destination $Destination
Set-Content -LiteralPath $Marker -Value $Backup
if ((Get-FileHash -LiteralPath $Destination -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $Source -Algorithm SHA256).Hash) { throw 'Hash mismatch' }
Write-Host "AGENT UPLOAD CLIENT INSTALLED (SOURCE ONLY). Backup marker: $Marker"
Write-Host 'No IPC, consent popup, capture or end-to-end stream has been activated.'
