#Requires -Version 5.1

param(
    [string]$BackendBaseUrl =
        "http://127.0.0.1:8001"
)

$ErrorActionPreference =
    "Stop"

Write-Host ""
Write-Host "==============================================="
Write-Host " WorkforceOS Phase 10 OpenAPI Verification"
Write-Host "==============================================="
Write-Host ""

$OpenApiUrl =
    "$BackendBaseUrl/openapi.json"

$OpenApi =
    Invoke-RestMethod `
        -Uri $OpenApiUrl `
        -Method Get

$Paths =
    $OpenApi.paths.PSObject.Properties.Name

$RequiredPaths = @(
    "/api/v1/device-agent/app-observation",
    "/api/v1/device-agent/app-status"
)

foreach ($RequiredPath in $RequiredPaths)
{
    if (
        $Paths -notcontains $RequiredPath
    )
    {
        throw (
            "Required Phase 10 route missing: " +
            $RequiredPath
        )
    }

    Write-Host (
        "PASS route registered: " +
        $RequiredPath
    )
}

Write-Host ""
Write-Host "==============================================="
Write-Host " PHASE 10 OPENAPI: PASS"
Write-Host "==============================================="
Write-Host ""