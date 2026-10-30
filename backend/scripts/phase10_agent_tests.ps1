#Requires -Version 5.1

$ErrorActionPreference = "Stop"

$AgentRoot =
    "C:\workforce-os\agent"

$AgentProject =
    Join-Path `
        $AgentRoot `
        "WorkforceOS.Agent\WorkforceOS.Agent.csproj"

$TestProject =
    Join-Path `
        $AgentRoot `
        "WorkforceOS.Agent.Tests\WorkforceOS.Agent.Tests.csproj"

Write-Host ""
Write-Host "================================================="
Write-Host " WorkforceOS Phase 10 Agent Tests"
Write-Host "================================================="
Write-Host ""

Write-Host "[1/2] Building Agent..."

dotnet build `
    $AgentProject `
    --configuration Release

if ($LASTEXITCODE -ne 0)
{
    throw "Phase 10 Agent build failed."
}

Write-Host "PASS Agent build"
Write-Host ""

Write-Host "[2/2] Running Agent tests..."

dotnet test `
    $TestProject `
    --configuration Release `
    --no-restore

if ($LASTEXITCODE -ne 0)
{
    throw "Phase 10 Agent tests failed."
}

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 10 AGENT TESTS: PASS"
Write-Host "================================================="