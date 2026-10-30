#Requires -Version 5.1

$ErrorActionPreference = "Stop"

$BackendRoot = "C:\workforce-os\backend"
$AgentRoot = "C:\workforce-os\agent"
$Python = "C:\workforce-os\.venv\Scripts\python.exe"

Write-Host ""
Write-Host "================================================="
Write-Host " WorkforceOS Phase 11 Live Acceptance"
Write-Host "================================================="
Write-Host ""

Write-Host "[1/6] Tenant schema..."

Set-Location $BackendRoot

.\scripts\phase11_verify_tenant_schema.ps1

if ($LASTEXITCODE -ne 0)
{
    throw "Tenant schema gate failed."
}

Write-Host ""
Write-Host "[2/6] Backend contract..."

.\scripts\phase11_backend_gate.ps1

if ($LASTEXITCODE -ne 0)
{
    throw "Backend gate failed."
}

Write-Host ""
Write-Host "[3/6] OpenAPI..."

.\scripts\phase11_verify_openapi.ps1

if ($LASTEXITCODE -ne 0)
{
    throw "OpenAPI gate failed."
}

Write-Host ""
Write-Host "[4/6] Browser integration..."

Set-Location $AgentRoot

.\scripts\phase11_verify_browser_hosts.ps1

if ($LASTEXITCODE -ne 0)
{
    throw "Browser host verification failed."
}

Write-Host ""
Write-Host "[5/6] Live database privacy..."

Set-Location $BackendRoot

& $Python `
    .\scripts\phase11_verify_live_database.py

if ($LASTEXITCODE -ne 0)
{
    throw "Live database verification failed."
}

Write-Host ""
Write-Host "[6/6] Domain switching..."

& $Python `
    .\scripts\phase11_domain_switch_check.py

if ($LASTEXITCODE -ne 0)
{
    throw "Domain-switch verification failed."
}

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 11 WEBSITE TRACKING: LIVE ACCEPTANCE PASS"
Write-Host "================================================="
Write-Host ""