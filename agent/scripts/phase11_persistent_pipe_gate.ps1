#Requires -Version 5.1

$ErrorActionPreference = "Stop"

$AgentRoot = "C:\workforce-os\agent"
$Python = "C:\workforce-os\.venv\Scripts\python.exe"

Write-Host ""
Write-Host "==============================================="
Write-Host " WorkforceOS Phase 11 Persistent Pipe Gate"
Write-Host "==============================================="
Write-Host ""

Write-Host "[1/4] Production build..."

dotnet build `
    "$AgentRoot\WorkforceOS.Agent\WorkforceOS.Agent.csproj" `
    --configuration Release

if ($LASTEXITCODE -ne 0)
{
    throw "Persistent pipe production build failed."
}

Write-Host "PASS production build"

Write-Host ""
Write-Host "[2/4] Agent tests..."

dotnet test `
    "$AgentRoot\WorkforceOS.Agent.Tests\WorkforceOS.Agent.Tests.csproj" `
    --configuration Release

if ($LASTEXITCODE -ne 0)
{
    throw "Persistent pipe tests failed."
}

Write-Host "PASS Agent tests"

Write-Host ""
Write-Host "[3/4] Native-host smoke test..."

& $Python `
    "$AgentRoot\scripts\phase11_native_host_smoke_test.py"

if ($LASTEXITCODE -ne 0)
{
    throw "Native-host smoke test failed."
}

Write-Host "PASS native-host smoke test"

Write-Host ""
Write-Host "[4/4] Persistent pipe stress..."

& $Python `
    "$AgentRoot\scripts\phase11_pipe_stress_test.py"

if ($LASTEXITCODE -ne 0)
{
    throw "Persistent pipe stress test failed."
}

Write-Host ""
Write-Host "==============================================="
Write-Host " PHASE 11 PERSISTENT PIPE GATE: PASS"
Write-Host "==============================================="
Write-Host ""