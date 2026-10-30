#Requires -Version 5.1

$ErrorActionPreference = "Stop"

$BackendRoot = "C:\workforce-os\backend"
$Python = "C:\workforce-os\.venv\Scripts\python.exe"

Set-Location $BackendRoot

Write-Host ""
Write-Host "==============================================="
Write-Host " WorkforceOS Phase 11 Tenant Migration"
Write-Host "==============================================="
Write-Host ""

& $Python `
    .\scripts\phase11_apply_tenant_migration.py

if ($LASTEXITCODE -ne 0)
{
    throw "Phase 11 tenant migration failed."
}

Write-Host ""
Write-Host "==============================================="
Write-Host " PHASE 11 TENANT MIGRATION: PASS"
Write-Host "==============================================="
Write-Host ""