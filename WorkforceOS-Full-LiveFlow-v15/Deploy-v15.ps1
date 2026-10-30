param(
  [switch]$Agent,
  [switch]$Companion,
  [switch]$Apply,
  [string]$Root = 'C:\workforce-os'
)
$ErrorActionPreference='Stop'
if (!$Agent -and !$Companion) { throw 'Select -Agent or -Companion. Nothing deployed.' }
$Roles = @()
if ($Agent) { $Roles += @{ Name='Agent'; Stage='artifacts\agent-v15-staging'; Live='artifacts\agent\win-x64'; File='WorkforceOS.Agent.dll' } }
if ($Companion) { $Roles += @{ Name='Companion'; Stage='artifacts\screen-companion-v15-staging'; Live='artifacts\screen-companion'; File='WorkforceOS.ScreenCompanion.dll' } }
foreach ($Role in $Roles) {
  $Stage = Join-Path $Root $Role.Stage
  $Live = Join-Path $Root $Role.Live
  if (!(Test-Path (Join-Path $Stage $Role.File))) { throw "Missing staging build: $Stage" }
  if (!(Test-Path (Join-Path $Live $Role.File))) { throw "Missing live installation: $Live" }
  Write-Host "$($Role.Name) STAGED SHA256: $((Get-FileHash (Join-Path $Stage $Role.File)).Hash)"
  Write-Host "$($Role.Name) LIVE   SHA256: $((Get-FileHash (Join-Path $Live $Role.File)).Hash)"
}
if (!$Apply) { Write-Host 'DEPLOYMENT PREFLIGHT PASS. No services/processes changed.' -ForegroundColor Green; exit 0 }
if ($Companion) {
  $Running=Get-Process 'WorkforceOS.ScreenCompanion' -ErrorAction SilentlyContinue
  if ($Running) {throw 'Companion still running. Employee must stop sharing, then pause the interactive supervisor first. This installer WILL NOT kill its supervisor.'}
}
$Backup = Join-Path $Root ('WorkforceOS-v15-binaries-backup-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
New-Item -ItemType Directory -Force -Path $Backup | Out-Null
$AgentStopped = $false
try {
  if ($Agent) {
    $Svc = Get-Service -Name 'WorkforceOSAgent' -ErrorAction Stop
    if ($Svc.Status -eq 'Running') {
      Stop-Service 'WorkforceOSAgent' -ErrorAction Stop
      $Svc.WaitForStatus('Stopped',[TimeSpan]::FromSeconds(40))
      $AgentStopped = $true
    }
    if (Get-Process 'WorkforceOS.Agent' -ErrorAction SilentlyContinue) {
      throw 'Agent process is still running; refuse to overwrite locked files.'
    }
  }
  foreach ($Role in $Roles) {
    $Stage=Join-Path $Root $Role.Stage
    $Live=Join-Path $Root $Role.Live
    $TargetBackup=Join-Path $Backup $Role.Name
    Copy-Item -LiteralPath $Live -Destination $TargetBackup -Recurse -Force -ErrorAction Stop
    Copy-Item -Path (Join-Path $Stage '*') -Destination $Live -Recurse -Force -ErrorAction Stop
    if ((Get-FileHash (Join-Path $Stage $Role.File)).Hash -ne (Get-FileHash (Join-Path $Live $Role.File)).Hash) {
      throw "Deployment verification failed: $($Role.Name)"
    }
    Write-Host "$($Role.Name) V15 DEPLOYMENT VERIFIED" -ForegroundColor Green
  }
} catch {
  Write-Warning "Deployment failed. Backup is at $Backup. Review and restore the original binaries before restarting."
  throw
} finally {
  if ($AgentStopped) {
    Start-Service 'WorkforceOSAgent' -ErrorAction Stop
    (Get-Service 'WorkforceOSAgent').WaitForStatus('Running',[TimeSpan]::FromSeconds(40))
    Write-Host 'WorkforceOSAgent restarted.'
  }
}
Write-Host "Backup: $Backup"
Write-Host 'Restart your existing interactive Companion supervisor if it was paused.'
