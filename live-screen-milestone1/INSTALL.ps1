#Requires -Version 5.1
param([string]$Root = 'C:\workforce-os')
$ErrorActionPreference = 'Stop'
$Project = Join-Path $PSScriptRoot 'agent\WorkforceOS.ScreenCompanion'
$Target = Join-Path $Root 'agent\WorkforceOS.ScreenCompanion'
if (!(Test-Path -LiteralPath $Root)) { throw "Project root missing: $Root" }
if (!(Get-Command dotnet -ErrorAction SilentlyContinue)) { throw 'Install .NET 8 SDK first (dotnet executable not found).' }
if (!(Test-Path (Join-Path $Root 'agent\WorkforceOS.Agent\WorkforceOS.Agent.csproj'))) { throw 'Unexpected WorkforceOS project structure.' }
New-Item -Path $Target -ItemType Directory -Force | Out-Null
$Stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
if (Test-Path (Join-Path $Target 'Program.cs')) {
  $Backup = Join-Path $Root "backup-screencompanion-$Stamp"
  Copy-Item -LiteralPath $Target -Destination $Backup -Recurse -Force
  Write-Host "Backup: $Backup"
}
Copy-Item -Path (Join-Path $Project '*') -Destination $Target -Force
Write-Host 'Building employee-visible LOCAL preview companion...'
& dotnet build (Join-Path $Target 'WorkforceOS.ScreenCompanion.csproj') -c Release
if ($LASTEXITCODE -ne 0) { throw 'Companion build failed.' }
Write-Host 'PASS: Native companion compiled.' -ForegroundColor Green
Write-Host 'To run in EMPLOYEE logged-in desktop (not as a Windows service):'
Write-Host "dotnet run --project `"$(Join-Path $Target 'WorkforceOS.ScreenCompanion.csproj')`" -c Release --no-build"
Write-Host 'Note: This is local preview only. No backend streaming or owner viewer connected.' -ForegroundColor Yellow
