param([switch]$Apply)
$ErrorActionPreference = 'Stop'
$Root = 'C:\workforce-os'
$Target = Join-Path $Root 'agent\WorkforceOS.Agent\LiveScreen\LiveScreenInboxWorker.cs'
$Patcher = Join-Path $PSScriptRoot 'patch.py'
$Python = 'python'
$VenvPython = Join-Path $Root '.venv\Scripts\python.exe'
if (Test-Path $VenvPython) { $Python = $VenvPython }
if (!(Test-Path $Target)) { throw "Agent source missing: $Target" }
$Stage = Join-Path $env:TEMP ('wfos-v8-'+[guid]::NewGuid().ToString('N')+'.cs')
Copy-Item -LiteralPath $Target -Destination $Stage -ErrorAction Stop
try {
  & $Python $Patcher $Stage
  if ($LASTEXITCODE -ne 0) { throw 'Source compatibility check FAILED' }
  Write-Host 'PREFLIGHT PASS: inbox accepted-session activation recovery'
  if (-not $Apply) { Write-Host 'DRY RUN ONLY. Use -Apply.'; return }
  $Backup = Join-Path $Root ('WorkforceOS-v8-backup-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
  New-Item -ItemType Directory -Force -Path $Backup | Out-Null
  Copy-Item -LiteralPath $Target -Destination (Join-Path $Backup 'LiveScreenInboxWorker.cs') -ErrorAction Stop
  Copy-Item -LiteralPath $Stage -Destination $Target -Force -ErrorAction Stop
  Write-Host "APPLIED. Backup: $Backup"
  Write-Host 'NEXT: dotnet publish Agent to staging, then deploy via your service-safe deployment process.'
} finally { Remove-Item $Stage -Force -ErrorAction SilentlyContinue }
