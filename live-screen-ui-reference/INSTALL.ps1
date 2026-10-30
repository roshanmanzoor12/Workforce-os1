param([string]$Root='C:\workforce-os')
$ErrorActionPreference='Stop'
$src=Join-Path $PSScriptRoot 'page.tsx'
$target=Join-Path $Root 'apps\web\app\(workspace)\monitoring\live-screen\page.tsx'
$comp=Join-Path $Root 'apps\web\components\monitoring\native-jpeg-stream.tsx'
if (!(Test-Path -LiteralPath $target)) { throw "Original page missing: $target" }
if (!(Test-Path -LiteralPath $comp)) { throw "NativeJpegStream component missing. Install Milestone 3D first: $comp" }
if (!(Test-Path -LiteralPath $src)) { throw "Package missing page.tsx" }
$original=Get-Content -LiteralPath $target -Raw
if ($original -notmatch 'export default function LiveScreenPage') { throw 'Existing page is not the expected LiveScreenPage. No changes made.' }
$backupDir=Join-Path $Root 'artifacts\live-screen-ui-backups'
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
$backup=Join-Path $backupDir ('page-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.tsx')
Copy-Item -LiteralPath $target -Destination $backup
Copy-Item -LiteralPath $src -Destination $target -Force
$latest=Join-Path $backupDir 'LATEST-BACKUP.txt'
Set-Content -LiteralPath $latest -Value $backup -Encoding UTF8
Write-Host 'PASS: Original Live Screen page replaced.' -ForegroundColor Green
Write-Host "Backup: $backup"
Write-Host 'Restart the Next.js frontend. Existing local relay and employee-visible companion remain unchanged.'
Write-Warning 'This package is an owner UI replacement only. It does not authorize silent capture or implement production media authorization.'
