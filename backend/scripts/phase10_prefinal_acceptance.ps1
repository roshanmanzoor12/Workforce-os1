#Requires -Version 5.1

$ErrorActionPreference = "Stop"

$BackendRoot =
    "C:\workforce-os\backend"

$AgentRoot =
    "C:\workforce-os\agent"

$Python =
    "C:\workforce-os\.venv\Scripts\python.exe"

Write-Host ""
Write-Host "================================================="
Write-Host " WorkforceOS Phase 10 Pre-Final Acceptance"
Write-Host "================================================="
Write-Host ""

Write-Host "[1/5] Backend App Tracking tests..."

Push-Location $BackendRoot

try
{
    & $Python `
        -m pytest `
        tests\modules\app_tracking `
        -v

    if ($LASTEXITCODE -ne 0)
    {
        throw "Backend App Tracking tests failed."
    }
}
finally
{
    Pop-Location
}

Write-Host "PASS backend tests"
Write-Host ""

Write-Host "[2/5] Agent production build..."

dotnet build `
    "$AgentRoot\WorkforceOS.Agent\WorkforceOS.Agent.csproj" `
    --configuration Release

if ($LASTEXITCODE -ne 0)
{
    throw "Agent production build failed."
}

Write-Host "PASS Agent build"
Write-Host ""

Write-Host "[3/5] Agent tests..."

dotnet test `
    "$AgentRoot\WorkforceOS.Agent.Tests\WorkforceOS.Agent.Tests.csproj" `
    --configuration Release

if ($LASTEXITCODE -ne 0)
{
    throw "Agent test project failed."
}

Write-Host "PASS Agent tests"
Write-Host ""

Write-Host "[4/5] Phase 10 tenant migration..."

& "$BackendRoot\scripts\phase10_apply_tenant_migration.ps1"

if ($LASTEXITCODE -ne 0)
{
    throw "Phase 10 migration verification failed."
}

Write-Host "PASS migration"
Write-Host ""

Write-Host "[5/5] Checking required integration files..."

$RequiredFiles = @(
    "$AgentRoot\WorkforceOS.Agent\AppTracking\AppTrackingSessionHelperRunner.cs",
    "$AgentRoot\WorkforceOS.Agent\AppTracking\AppTrackingBackendReporter.cs",
    "$AgentRoot\WorkforceOS.Agent\AppTracking\AppTrackingServiceReceiver.cs",
    "$AgentRoot\WorkforceOS.Agent\AppTracking\AppTrackingServiceCollectionExtensions.cs",
    "$BackendRoot\app\modules\app_tracking\agent_router.py",
    "$BackendRoot\app\modules\app_tracking\status_router.py"
)

foreach ($File in $RequiredFiles)
{
    if (-not (Test-Path $File))
    {
        throw "Missing required file: $File"
    }
}

Write-Host "PASS required integration files"
Write-Host ""

Write-Host "================================================="
Write-Host " PHASE 10 PRE-FINAL ACCEPTANCE: PASS"
Write-Host "================================================="
Write-Host ""
Write-Host "Remaining:"
Write-Host " - Program.cs registration"
Write-Host " - appsettings.json AppTracking section"
Write-Host " - backend main.py router registration"
Write-Host " - publish/restart"
Write-Host " - live app observation"
Write-Host " - live app switch acceptance"
Write-Host ""