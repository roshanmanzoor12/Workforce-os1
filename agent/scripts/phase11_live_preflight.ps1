#Requires -Version 5.1

$ErrorActionPreference = "Stop"

$BackendUrl = "http://127.0.0.1:8001"

$AgentExe = (
    "C:\workforce-os\artifacts\agent\win-x64\" +
    "WorkforceOS.Agent.exe"
)

$NativeHostExe = (
    "C:\workforce-os\artifacts\website-native-host\" +
    "WorkforceOS.WebsiteNativeHost.exe"
)

$ExtensionRoot = (
    "C:\workforce-os\extensions\workforce-browser"
)

Write-Host ""
Write-Host "==============================================="
Write-Host " WorkforceOS Phase 11 Live Preflight"
Write-Host "==============================================="
Write-Host ""

Write-Host "[1/6] Backend..."

try
{
    $OpenApi = Invoke-RestMethod `
        -Uri ($BackendUrl + "/openapi.json") `
        -Method Get
}
catch
{
    throw (
        "Backend is not reachable at " +
        $BackendUrl
    )
}

Write-Host "PASS backend reachable"

Write-Host ""
Write-Host "[2/6] Website API..."

$WebsitePath = (
    "/api/v1/device-agent/website-observation"
)

$PathProperty = (
    $OpenApi.paths.PSObject.Properties[
        $WebsitePath
    ]
)

if ($null -eq $PathProperty)
{
    throw "Website observation API missing from OpenAPI."
}

Write-Host "PASS website observation API"

Write-Host ""
Write-Host "[3/6] Agent artifact..."

if (-not (Test-Path $AgentExe))
{
    throw "Agent artifact missing."
}

Write-Host "PASS Agent artifact"

Write-Host ""
Write-Host "[4/6] Native host artifact..."

if (-not (Test-Path $NativeHostExe))
{
    throw "Native host artifact missing."
}

Write-Host "PASS Native host artifact"

Write-Host ""
Write-Host "[5/6] Extension..."

$ManifestPath = Join-Path `
    $ExtensionRoot `
    "manifest.json"

$WorkerPath = Join-Path `
    $ExtensionRoot `
    "service_worker.js"

if (-not (Test-Path $ManifestPath))
{
    throw "Extension manifest missing."
}

if (-not (Test-Path $WorkerPath))
{
    throw "Extension worker missing."
}

Write-Host "PASS extension files"

Write-Host ""
Write-Host "[6/6] Agent service..."

$Service = Get-Service `
    -Name "WorkforceOSAgent" `
    -ErrorAction Stop

if ($Service.Status -ne "Running")
{
    throw "WorkforceOS Agent service is not running."
}

Write-Host "PASS Agent service"

Write-Host ""
Write-Host "==============================================="
Write-Host " PHASE 11 LIVE PREFLIGHT: PASS"
Write-Host "==============================================="
Write-Host ""