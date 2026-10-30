#Requires -Version 5.1
$ErrorActionPreference = 'Stop'
$Page = 'C:\workforce-os\apps\web\app\(workspace)\monitoring\live-screen\page.tsx'
$Backup = @(Get-ChildItem -LiteralPath (Split-Path -Parent $Page) -Filter 'page.tsx.backup-*' -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1)
if (!$Backup) { throw 'No backup found.' }
Copy-Item -LiteralPath $Backup[0].FullName -Destination $Page -Force
Write-Host "Restored $($Backup[0].FullName)" -ForegroundColor Green
