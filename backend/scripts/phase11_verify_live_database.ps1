#Requires -Version 5.1

$ErrorActionPreference = "Stop"

$BackendRoot = "C:\workforce-os\backend"
$Python = "C:\workforce-os\.venv\Scripts\python.exe"

Set-Location $BackendRoot

Write-Host ""
Write-Host "==============================================="
Write-Host " WorkforceOS Phase 11 Live DB Verification"
Write-Host "==============================================="
Write-Host ""

& $Python `
    .\scripts\phase11_verify_live_database.py

if ($LASTEXITCODE -ne 0)
{
    throw "Phase 11 live database verification failed."
}

Write-Host ""
Write-Host "==============================================="
Write-Host " PHASE 11 LIVE DATABASE CHECK: PASS"
Write-Host "==============================================="
Write-Host ""