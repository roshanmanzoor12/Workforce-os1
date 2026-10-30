#Requires -Version 5.1

$ErrorActionPreference = "Stop"

$BackendRoot = "C:\workforce-os\backend"
$AgentRoot = "C:\workforce-os\agent"
$Python = "C:\workforce-os\.venv\Scripts\python.exe"

Write-Host ""
Write-Host "=================================================="
Write-Host " WorkforceOS Phase 11 Final Completion Gate"
Write-Host "=================================================="
Write-Host ""

Write-Host "[1/7] Tenant schema..."

Set-Location $BackendRoot

.\scripts\phase11_verify_tenant_schema.ps1

Write-Host ""
Write-Host "[2/7] Backend tests..."

.\scripts\phase11_backend_gate.ps1

Write-Host ""
Write-Host "[3/7] OpenAPI..."

.\scripts\phase11_verify_openapi.ps1

Write-Host ""
Write-Host "[4/7] Agent reporting..."

Set-Location $AgentRoot

.\scripts\phase11_reporting_gate.ps1

Write-Host ""
Write-Host "[5/7] Native browser host..."

.\scripts\phase11_verify_browser_hosts.ps1

Write-Host ""
Write-Host "[6/7] Live persistence + privacy..."

Set-Location $BackendRoot

& $Python `
    .\scripts\phase11_verify_live_database.py

if ($LASTEXITCODE -ne 0)
{
    throw "Phase 11 live persistence gate failed."
}

Write-Host ""
Write-Host "[7/7] Domain switching..."

& $Python `
    .\scripts\phase11_domain_switch_check.py

if ($LASTEXITCODE -ne 0)
{
    throw "Phase 11 domain-switch gate failed."
}

Write-Host ""
Write-Host "=================================================="
Write-Host " PHASE 11 WEBSITE TRACKING: 100% PASS"
Write-Host "=================================================="
Write-Host ""