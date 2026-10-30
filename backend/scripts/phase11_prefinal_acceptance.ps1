#Requires -Version 5.1

$ErrorActionPreference = "Stop"

$BackendRoot = "C:\workforce-os\backend"
$AgentRoot = "C:\workforce-os\agent"

Write-Host ""
Write-Host "=================================================="
Write-Host " WorkforceOS Phase 11 Pre-Final Acceptance"
Write-Host "=================================================="
Write-Host ""

Write-Host "[1/5] Backend code/tests..."

Set-Location $BackendRoot

.\scripts\phase11_backend_gate.ps1

if ($LASTEXITCODE -ne 0)
{
    throw "Phase 11 backend gate failed."
}

Write-Host ""
Write-Host "[2/5] Tenant schema..."

.\scripts\phase11_verify_tenant_schema.ps1

if ($LASTEXITCODE -ne 0)
{
    throw "Phase 11 tenant schema gate failed."
}

Write-Host ""
Write-Host "[3/5] OpenAPI..."

.\scripts\phase11_verify_openapi.ps1

if ($LASTEXITCODE -ne 0)
{
    throw "Phase 11 OpenAPI gate failed."
}

Write-Host ""
Write-Host "[4/5] Agent..."

Set-Location $AgentRoot

.\scripts\phase11_agent_gate.ps1

if ($LASTEXITCODE -ne 0)
{
    throw "Phase 11 Agent gate failed."
}

Write-Host ""
Write-Host "[5/5] Extension files..."

$ExtensionRoot = (
    "C:\workforce-os\extensions\workforce-browser"
)

$RequiredFiles = @(
    "$ExtensionRoot\manifest.json",
    "$ExtensionRoot\service_worker.js"
)

foreach ($File in $RequiredFiles)
{
    if (-not (Test-Path $File))
    {
        throw (
            "Required extension file missing: " +
            $File
        )
    }

    Write-Host (
        "PASS file: " +
        $File
    )
}

Write-Host ""
Write-Host "=================================================="
Write-Host " PHASE 11 PRE-FINAL ACCEPTANCE: PASS"
Write-Host "=================================================="
Write-Host ""
Write-Host "Remaining:"
Write-Host " - credential adapter"
Write-Host " - reporting worker activation"
Write-Host " - extension/native-host registration"
Write-Host " - live domain observations"
Write-Host " - domain switch acceptance"
Write-Host ""