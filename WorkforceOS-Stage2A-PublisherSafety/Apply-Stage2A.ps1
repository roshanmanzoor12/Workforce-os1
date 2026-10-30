param([switch]$Apply)
$ErrorActionPreference = 'Stop'
$Root = 'C:\workforce-os'
$Rel = 'agent\WorkforceOS.ScreenCompanion\RemoteFramePublisher.cs'
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$Source = Join-Path $Here (Join-Path 'patch' $Rel)
$Target = Join-Path $Root $Rel
$Expected = '357da2f82d47c9c90616a1a8749fd235cd51c80de52178cb68c6ff4e2724a67f'
if (!(Test-Path -LiteralPath $Target)) { throw "Missing: $Target" }
if (!(Test-Path -LiteralPath $Source)) { throw "Missing patch source: $Source" }
$Actual = (Get-FileHash -LiteralPath $Target -Algorithm SHA256).Hash.ToLowerInvariant()
Write-Host "Current source SHA256: $Actual"
if ($Actual -ne $Expected) { throw 'Source hash differs from audited ZIP. No changes applied.' }
Write-Host 'Hash verified.' -ForegroundColor Green
if (!$Apply) { Write-Host 'DRY RUN complete. To apply, rerun with -Apply.'; return }
$BackupDir = Join-Path $Root ('workforce-patch-backups\stage2a-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
$Backup = Join-Path $BackupDir $Rel
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Backup) | Out-Null
Copy-Item -LiteralPath $Target -Destination $Backup
Copy-Item -LiteralPath $Source -Destination $Target -Force
Write-Host "Patched source: $Target" -ForegroundColor Green
Write-Host "Backup: $Backup"
Write-Host 'No Windows service or database was changed.'
Write-Host 'Rebuild + test ScreenCompanion separately; do NOT deploy until test passes.' -ForegroundColor Yellow
