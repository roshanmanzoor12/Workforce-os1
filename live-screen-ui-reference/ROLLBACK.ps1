param([string]$Root='C:\workforce-os')
$ErrorActionPreference='Stop'
$dir=Join-Path $Root 'artifacts\live-screen-ui-backups'
$record=Join-Path $dir 'LATEST-BACKUP.txt'
if (!(Test-Path -LiteralPath $record)) { throw "No recorded backup: $record" }
$backup=(Get-Content -LiteralPath $record -Raw).Trim()
if (!(Test-Path -LiteralPath $backup)) { throw "Backup not found: $backup" }
$target=Join-Path $Root 'apps\web\app\(workspace)\monitoring\live-screen\page.tsx'
Copy-Item -LiteralPath $backup -Destination $target -Force
Write-Host "Restored: $backup" -ForegroundColor Green
