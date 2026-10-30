#Requires -Version 5.1

$ErrorActionPreference =
    "Stop"

$BackendRoot =
    "C:\workforce-os\backend"

$AgentRoot =
    "C:\workforce-os\agent"

$Python =
    "C:\workforce-os\.venv\Scripts\python.exe"

Write-Host ""
Write-Host "================================================="
Write-Host " WorkforceOS Phase 10 Completion Gate"
Write-Host "================================================="
Write-Host ""

Write-Host "[1/7] Production Agent tree cleanliness..."

$UnexpectedTests =
    Get-ChildItem `
        "$AgentRoot\WorkforceOS.Agent" `
        -Recurse `
        -Filter "*Tests.cs"

if ($UnexpectedTests.Count -gt 0)
{
    $UnexpectedTests |
        Select-Object FullName

    throw (
        "Test files found in production Agent project."
    )
}

Write-Host "PASS production tree"
Write-Host ""

Write-Host "[2/7] Production Agent build..."

dotnet build `
    "$AgentRoot\WorkforceOS.Agent\WorkforceOS.Agent.csproj" `
    --configuration Release

if ($LASTEXITCODE -ne 0)
{
    throw (
        "Production Agent build failed."
    )
}

Write-Host "PASS Agent build"
Write-Host ""

Write-Host "[3/7] Agent tests..."

dotnet test `
    "$AgentRoot\WorkforceOS.Agent.Tests\WorkforceOS.Agent.Tests.csproj" `
    --configuration Release

if ($LASTEXITCODE -ne 0)
{
    throw (
        "Agent tests failed."
    )
}

Write-Host "PASS Agent tests"
Write-Host ""

Write-Host "[4/7] Backend tests..."

Push-Location $BackendRoot

try
{
    & $Python `
        -m pytest `
        tests\modules\app_tracking `
        -v

    if ($LASTEXITCODE -ne 0)
    {
        throw (
            "Backend App Tracking tests failed."
        )
    }
}
finally
{
    Pop-Location
}

Write-Host "PASS backend tests"
Write-Host ""

Write-Host "[5/7] Migration/OpenAPI verification..."

& "$BackendRoot\scripts\phase10_apply_tenant_migration.ps1"

& "$BackendRoot\scripts\phase10_verify_openapi.ps1"

Write-Host "PASS migration/OpenAPI"
Write-Host ""

Write-Host "[6/7] Live persistence..."

& "$BackendRoot\scripts\phase10_verify_live_app_tracking.ps1"

& "$BackendRoot\scripts\phase10_verify_interval_progress.ps1"

Write-Host "PASS live persistence/progression"
Write-Host ""

Write-Host "[7/7] App-switch sequence..."

& "$BackendRoot\scripts\phase10_verify_switch_sequence.ps1"

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 10 APP TRACKING: 100% ACCEPTANCE PASS"
Write-Host "================================================="
Write-Host ""