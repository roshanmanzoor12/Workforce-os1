#Requires -Version 5.1
$ErrorActionPreference = 'Stop'
$Root = 'C:\workforce-os'
$Page = Join-Path $Root 'apps\web\app\(workspace)\monitoring\live-screen\page.tsx'
$Backups = @(Get-ChildItem -LiteralPath (Split-Path $Page) -File -Filter 'page.tsx.backup-2c-*' | Sort-Object LastWriteTime -Descending)
if ($Backups.Count -eq 0) { throw 'Milestone 2C page backup not found.' }
Copy-Item -LiteralPath $Backups[0].FullName -Destination $Page -Force
Write-Host 'Restored original Live Screen page from:' $Backups[0].FullName
Write-Host 'The reusable native-live-video.tsx component was retained; it is harmless when unused.'
