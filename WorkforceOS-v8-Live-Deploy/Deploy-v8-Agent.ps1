param([switch]$Apply,[switch]$Rollback,[string]$BackupPath)
$ErrorActionPreference='Stop'
$Root='C:\workforce-os'
$Source=Join-Path $Root 'artifacts\agent-v8-staging'
$Dest=Join-Path $Root 'artifacts\agent\win-x64'
$ServiceName='WorkforceOSAgent'
$Dll='WorkforceOS.Agent.dll'
if (-not (Test-Path (Join-Path $Dest $Dll))) { throw "Installed Agent missing: $Dest" }
$svc=Get-Service -Name $ServiceName -ErrorAction Stop
if ($Rollback) {
  if (-not $BackupPath -or -not (Test-Path (Join-Path $BackupPath $Dll))) {throw 'Use -Rollback -BackupPath <printed backup path>'}
  Write-Host "ROLLBACK requested from $BackupPath" -ForegroundColor Yellow
  Stop-Service -Name $ServiceName -ErrorAction Stop
  $svc.WaitForStatus('Stopped',[timespan]::FromSeconds(40))
  try {
    Copy-Item -Path (Join-Path $BackupPath '*') -Destination $Dest -Recurse -Force -ErrorAction Stop
    if ((Get-FileHash (Join-Path $Dest $Dll)).Hash -ne (Get-FileHash (Join-Path $BackupPath $Dll)).Hash) {throw 'Rollback hash mismatch'}
  } finally {Start-Service -Name $ServiceName -ErrorAction Stop}
  Write-Host 'ROLLBACK COMPLETE; service started' -ForegroundColor Green
  exit 0
}
if (-not (Test-Path (Join-Path $Source $Dll))) { throw "Staging Agent missing: $Source" }
$old=(Get-FileHash (Join-Path $Dest $Dll)).Hash
$new=(Get-FileHash (Join-Path $Source $Dll)).Hash
Write-Host "SERVICE: $($svc.Status)"; Write-Host "LIVE DLL SHA256: $old"; Write-Host "STAGED DLL SHA256: $new"
if (-not $Apply) {Write-Host 'PREFLIGHT ONLY. Re-run -Apply after employee has stopped live sharing.'; exit 0}
if ($old -eq $new) {Write-Host 'Already deployed. No service restart needed.'; exit 0}
$Backup=Join-Path $Root ('WorkforceOS-agent-live-backup-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Path $Backup -ErrorAction Stop | Out-Null
Copy-Item -Path (Join-Path $Dest '*') -Destination $Backup -Recurse -Force -ErrorAction Stop
if ((Get-FileHash (Join-Path $Backup $Dll)).Hash -ne $old) {throw 'Backup verification failed; no service stopped'}
Write-Host "BACKUP: $Backup" -ForegroundColor Cyan
Stop-Service -Name $ServiceName -ErrorAction Stop
$svc=Get-Service -Name $ServiceName
$svc.WaitForStatus('Stopped',[timespan]::FromSeconds(40))
$failure=$null
try {
  Copy-Item -Path (Join-Path $Source '*') -Destination $Dest -Recurse -Force -ErrorAction Stop
  if ((Get-FileHash (Join-Path $Dest $Dll)).Hash -ne $new) {throw 'Deployed DLL hash mismatch'}
} catch {$failure=$_; Write-Warning "Deploy failed; restoring backup: $_"; Copy-Item -Path (Join-Path $Backup '*') -Destination $Dest -Recurse -Force -ErrorAction Stop}
finally {Start-Service -Name $ServiceName -ErrorAction Stop}
$svc=Get-Service -Name $ServiceName
$svc.WaitForStatus('Running',[timespan]::FromSeconds(40))
if ($failure) {throw "Deploy rolled back; cause: $failure"}
Write-Host 'V8 LIVE AGENT DEPLOYMENT VERIFIED: PASS' -ForegroundColor Green
Write-Host "Backup path: $Backup"
Get-CimInstance Win32_Service -Filter "Name='WorkforceOSAgent'" | Select-Object Name, State, ProcessId, PathName
