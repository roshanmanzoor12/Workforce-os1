#Requires -Version 5.1

$ErrorActionPreference = "Stop"

$AgentRoot = "C:\workforce-os\agent"

Write-Host ""
Write-Host "==============================================="
Write-Host " WorkforceOS Phase 11 Agent Gate"
Write-Host "==============================================="
Write-Host ""

Write-Host "[1/4] Checking test placement..."

$ProductionTests = Get-ChildItem `
    "$AgentRoot\WorkforceOS.Agent" `
    -Recurse `
    -Filter "*Tests.cs" `
    -ErrorAction SilentlyContinue

if ($null -ne $ProductionTests)
{
    if ($ProductionTests.Count -gt 0)
    {
        $ProductionTests |
            Select-Object FullName

        throw "Test files found in production Agent project."
    }
}

Write-Host "PASS test placement"
Write-Host ""

Write-Host "[2/4] Building Agent..."

dotnet build `
    "$AgentRoot\WorkforceOS.Agent\WorkforceOS.Agent.csproj" `
    --configuration Release

if ($LASTEXITCODE -ne 0)
{
    throw "Phase 11 Agent build failed."
}

Write-Host "PASS Agent build"
Write-Host ""

Write-Host "[3/4] Building native host launcher..."

dotnet build `
    "$AgentRoot\WorkforceOS.WebsiteNativeHost\WorkforceOS.WebsiteNativeHost.csproj" `
    --configuration Release

if ($LASTEXITCODE -ne 0)
{
    throw "Phase 11 native host build failed."
}

Write-Host "PASS native host build"
Write-Host ""

Write-Host "[4/4] Running Agent tests..."

dotnet test `
    "$AgentRoot\WorkforceOS.Agent.Tests\WorkforceOS.Agent.Tests.csproj" `
    --configuration Release

if ($LASTEXITCODE -ne 0)
{
    throw "Phase 11 Agent tests failed."
}

Write-Host ""
Write-Host "==============================================="
Write-Host " PHASE 11 AGENT GATE: PASS"
Write-Host "==============================================="
Write-Host ""