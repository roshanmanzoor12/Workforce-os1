#Requires -Version 5.1

$ErrorActionPreference = "Stop"

$AgentRoot = "C:\workforce-os\agent"
$Python = "C:\workforce-os\.venv\Scripts\python.exe"

Write-Host ""
Write-Host "==============================================="
Write-Host " WorkforceOS Phase 11 Pipe ACK Gate"
Write-Host "==============================================="
Write-Host ""

Write-Host "[1/3] Build..."

dotnet build `
    "$AgentRoot\WorkforceOS.Agent\WorkforceOS.Agent.csproj" `
    --configuration Release

if ($LASTEXITCODE -ne 0)
{
    throw "Pipe ACK production build failed."
}

Write-Host "PASS production build"
Write-Host ""

Write-Host "[2/3] Tests..."

dotnet test `
    "$AgentRoot\WorkforceOS.Agent.Tests\WorkforceOS.Agent.Tests.csproj" `
    --configuration Release

if ($LASTEXITCODE -ne 0)
{
    throw "Pipe ACK tests failed."
}

Write-Host "PASS tests"
Write-Host ""

Write-Host "[3/3] Native-host acceptance..."

& $Python `
    "$AgentRoot\scripts\phase11_native_host_smoke_test.py"

if ($LASTEXITCODE -ne 0)
{
    throw "Native-host ACK smoke test failed."
}

Write-Host ""
Write-Host "==============================================="
Write-Host " PHASE 11 PIPE ACK GATE: PASS"
Write-Host "==============================================="
Write-Host ""