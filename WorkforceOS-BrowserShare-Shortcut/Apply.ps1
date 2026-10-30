param([switch]$Apply)
$ErrorActionPreference = "Stop"
$Project = "C:\workforce-os"
$Relative = 'apps\web\app\(workspace)\monitoring\live-screen\page.tsx'
$Target = Join-Path $Project $Relative
$Patch = Join-Path $PSScriptRoot ('patch\' + $Relative)
$Expected = "49D5026A64AF4F454F36699880187D02A569D15DA5AF996FAD73056EB90E854F"
if (-not (Test-Path -LiteralPath $Target)) { throw "Target missing: $Target" }
if (-not (Test-Path -LiteralPath $Patch)) { throw "Patch missing: $Patch" }
$Actual = (Get-FileHash -LiteralPath $Target -Algorithm SHA256).Hash
Write-Host "Current SHA256: $Actual"
if ($Actual -ne $Expected) { throw "Source changed since Stage 1; safe-apply aborted. Do not overwrite custom modifications." }
if (-not $Apply) { Write-Host "DRY RUN passed. Rerun with -Apply to install."; exit 0 }
$Backup = Join-Path $Project ("workforce-patch-backups\browser-share-shortcut-" + (Get-Date -Format 'yyyyMMdd-HHmmss'))
$BackupFile = Join-Path $Backup $Relative
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $BackupFile) | Out-Null
Copy-Item -LiteralPath $Target -Destination $BackupFile -Force
Copy-Item -LiteralPath $Patch -Destination $Target -Force
if ((Get-FileHash -LiteralPath $Target -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $Patch -Algorithm SHA256).Hash) { Copy-Item -LiteralPath $BackupFile -Destination $Target -Force; throw "Verification failed; original restored." }
Write-Host "Patch applied. Original backup: $BackupFile" -ForegroundColor Green
Write-Host "Restart/rebuild Next.js and open /browser-screen-share. Native agent streaming is NOT enabled." -ForegroundColor Yellow
