#Requires -Version 5.1

$ErrorActionPreference = "Stop"

$AgentProject =
    "C:\workforce-os\agent\WorkforceOS.Agent\WorkforceOS.Agent.csproj"

$AgentDirectory =
    "C:\workforce-os\agent\WorkforceOS.Agent"

$BackendBaseUrl =
    "http://127.0.0.1:8001"

$ActivityStatusUrl =
    "$BackendBaseUrl/api/v1/device-agent/activity-status"

Write-Host ""
Write-Host "============================================="
Write-Host " WorkforceOS Phase 08 Live Activity Smoke"
Write-Host "============================================="
Write-Host ""

if (-not (Test-Path $AgentProject))
{
    throw "Agent project not found: $AgentProject"
}

Write-Host "[1/4] Building agent..."

Push-Location $AgentDirectory

try
{
    dotnet build

    if ($LASTEXITCODE -ne 0)
    {
        throw "Agent build failed."
    }
}
finally
{
    Pop-Location
}

Write-Host "PASS agent build"
Write-Host ""

Write-Host "[2/4] Checking WorkforceOS service..."

$Service =
    Get-Service `
        -Name "WorkforceOSAgent" `
        -ErrorAction SilentlyContinue

if ($null -eq $Service)
{
    throw "WorkforceOSAgent Windows service is not installed."
}

if ($Service.Status -ne "Running")
{
    Write-Host "Starting WorkforceOSAgent service..."

    Start-Service `
        -Name "WorkforceOSAgent"

    Start-Sleep `
        -Seconds 3

    $Service =
        Get-Service `
            -Name "WorkforceOSAgent"
}

if ($Service.Status -ne "Running")
{
    throw "WorkforceOSAgent service is not running."
}

Write-Host "PASS service running"
Write-Host ""

Write-Host "[3/4] Starting interactive activity helper..."
Write-Host ""
Write-Host "The helper will run in this logged-in Windows session."
Write-Host "Leave it running for at least 20-30 seconds."
Write-Host ""
Write-Host "Press Ctrl+C after an observation has been sent."
Write-Host ""

Push-Location $AgentDirectory

try
{
    dotnet run `
        --project $AgentProject `
        -- `
        --activity-session-helper
}
finally
{
    Pop-Location
}

Write-Host ""
Write-Host "[4/4] Helper exited."
Write-Host ""
Write-Host "Now verify authenticated activity status using"
Write-Host "the agent/service final acceptance script."
Write-Host ""

Write-Host "============================================="
Write-Host " PHASE 08 LIVE HELPER SMOKE COMPLETE"
Write-Host "============================================="
Write-Host ""