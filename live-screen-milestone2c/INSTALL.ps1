#Requires -Version 5.1
$ErrorActionPreference = 'Stop'
$Root = 'C:\workforce-os'
$Python = Join-Path $Root 'backend\.venv\Scripts\python.exe'
if (!(Test-Path -LiteralPath $Python)) { $Python = 'python' }
& $Python (Join-Path $PSScriptRoot 'patch.py') $Root
if ($LASTEXITCODE -ne 0) { throw 'Milestone 2C patch failed. Review message above.' }
Write-Host 'Milestone 2C installed. The player accepts a MediaStream but native transport is NOT implemented.' -ForegroundColor Green
