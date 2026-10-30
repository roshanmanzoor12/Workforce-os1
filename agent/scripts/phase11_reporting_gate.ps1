#Requires -Version 5.1

$ErrorActionPreference = "Stop"

$AgentRoot = "C:\workforce-os\agent"

$AgentProject = (
    "$AgentRoot\WorkforceOS.Agent\" +
    "WorkforceOS.Agent.csproj"
)

$TestProject = (
    "$AgentRoot\WorkforceOS.Agent.Tests\" +
    "WorkforceOS.Agent.Tests.csproj"
)

Write-Host ""
Write-Host "==============================================="
Write-Host " WorkforceOS Phase 11 Reporting Gate"
Write-Host "==============================================="
Write-Host ""

Write-Host "[1/4] Production build..."

dotnet build `
    $AgentProject `
    --configuration Release

if ($LASTEXITCODE -ne 0)
{
    throw "Website Tracking production build failed."
}

Write-Host "PASS production build"

Write-Host ""
Write-Host "[2/4] Tests..."

dotnet test `
    $TestProject `
    --configuration Release

if ($LASTEXITCODE -ne 0)
{
    throw "Website Tracking tests failed."
}

Write-Host "PASS tests"

Write-Host ""
Write-Host "[3/4] Credential wiring source..."

$ServiceCollectionFile = (
    "$AgentRoot\WorkforceOS.Agent\WebsiteTracking\" +
    "WebsiteTrackingServiceCollectionExtensions.cs"
)

$ServiceCollectionText = Get-Content `
    $ServiceCollectionFile `
    -Raw

if (
    $ServiceCollectionText `
        -notmatch "DeviceCredentialStoreWebsiteTrackingAdapter"
)
{
    throw "Website Tracking credential adapter is not registered."
}

if (
    $ServiceCollectionText `
        -notmatch "WebsiteTrackingBackendReportingWorker"
)
{
    throw "Website Tracking backend worker is not registered."
}

Write-Host "PASS credential adapter registration"
Write-Host "PASS backend worker registration"

Write-Host ""
Write-Host "[4/4] Privacy configuration..."

$AppSettings = Get-Content `
    "$AgentRoot\WorkforceOS.Agent\appsettings.json" `
    -Raw |
ConvertFrom-Json

if ($AppSettings.WebsiteTracking.CaptureFullUrls -ne $false)
{
    throw "CaptureFullUrls must remain false."
}

if ($AppSettings.WebsiteTracking.CapturePageTitles -ne $false)
{
    throw "CapturePageTitles must remain false."
}

if (
    $AppSettings.WebsiteTracking.MonitoringDisclosureRequired `
    -ne $true
)
{
    throw "MonitoringDisclosureRequired must remain true."
}

Write-Host "PASS Website Tracking privacy configuration"

Write-Host ""
Write-Host "==============================================="
Write-Host " PHASE 11 REPORTING GATE: PASS"
Write-Host "==============================================="
Write-Host ""