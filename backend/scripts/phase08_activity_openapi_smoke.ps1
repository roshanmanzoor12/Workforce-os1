#Requires -Version 5.1

$ErrorActionPreference = "Stop"

$BaseUrl =
    "http://127.0.0.1:8001"

$OpenApiUrl =
    "$BaseUrl/openapi.json"

$ActivityStatePath =
    "/api/v1/device-agent/activity-state"

$ActivityStatusPath =
    "/api/v1/device-agent/activity-status"

Write-Host ""
Write-Host "============================================="
Write-Host " WorkforceOS Phase 08 Activity OpenAPI Smoke"
Write-Host "============================================="
Write-Host ""

try
{
    $Schema =
        Invoke-RestMethod `
            -Method Get `
            -Uri $OpenApiUrl `
            -TimeoutSec 10
}
catch
{
    throw (
        "Unable to reach WorkforceOS backend at " +
        $OpenApiUrl
    )
}

if ($null -eq $Schema.paths)
{
    throw (
        "OpenAPI response does not contain paths."
    )
}

$ActivityStateProperty =
    $Schema.paths.PSObject.Properties[
        $ActivityStatePath
    ]

$ActivityStatusProperty =
    $Schema.paths.PSObject.Properties[
        $ActivityStatusPath
    ]

if ($null -eq $ActivityStateProperty)
{
    throw (
        "Missing route: " +
        $ActivityStatePath
    )
}

if ($null -eq $ActivityStatusProperty)
{
    throw (
        "Missing route: " +
        $ActivityStatusPath
    )
}

if ($null -eq $ActivityStateProperty.Value.post)
{
    throw (
        "POST activity-state operation is missing."
    )
}

if ($null -eq $ActivityStatusProperty.Value.get)
{
    throw (
        "GET activity-status operation is missing."
    )
}

Write-Host (
    "PASS POST " +
    $ActivityStatePath
)

Write-Host (
    "PASS GET  " +
    $ActivityStatusPath
)

Write-Host ""
Write-Host "============================================="
Write-Host " PHASE 08 ACTIVITY OPENAPI SMOKE: PASS"
Write-Host "============================================="
Write-Host ""