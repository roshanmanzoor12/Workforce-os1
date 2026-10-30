#Requires -Version 5.1
$ErrorActionPreference = 'Stop'
$Root = 'C:\workforce-os'
$Page = Join-Path $Root 'apps\web\app\(workspace)\monitoring\live-screen\page.tsx'
if (!(Test-Path -LiteralPath $Page)) { throw "Original page not found: $Page" }
$Python = Join-Path $Root 'backend\.venv\Scripts\python.exe'
if (!(Test-Path -LiteralPath $Python)) { $Python = 'python' }
& $Python (Join-Path $PSScriptRoot 'patch.py') $Root
if ($LASTEXITCODE -ne 0) { throw 'Patch failed. No frontend changes made.' }
Write-Host 'Milestone 2B: Legacy nested browser demo removed where present.' -ForegroundColor Green
Write-Host 'This is UI cleanup only; native remote streaming is still NOT implemented.'
Write-Host 'Refresh http://localhost:3001/monitoring/live-screen'
