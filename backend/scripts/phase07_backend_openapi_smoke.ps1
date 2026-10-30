$ErrorActionPreference = "Stop"

$BaseUrl =
    "http://127.0.0.1:8001"

$OpenApiUrl =
    "$BaseUrl/openapi.json"

Write-Host ""
Write-Host "=============================================="
Write-Host " WorkforceOS Phase 07 Backend OpenAPI Smoke"
Write-Host "=============================================="
Write-Host ""

Write-Host "Checking backend..."

try
{
    $Response =
        Invoke-RestMethod `
            -Method Get `
            -Uri $OpenApiUrl `
            -TimeoutSec 10
}
catch
{
    throw (
        "Unable to load WorkforceOS OpenAPI from " +
        $OpenApiUrl +
        ". Make sure the backend is running."
    )
}

if (
    $null -eq $Response.paths
)
{
    throw "OpenAPI response does not contain paths."
}

$HeartbeatPath =
    "/api/v1/device-agent/heartbeat"

$PresencePath =
    "/api/v1/device-agent/presence"

$Heartbeat =
    $Response.paths.PSObject.Properties[
        $HeartbeatPath
    ]

$Presence =
    $Response.paths.PSObject.Properties[
        $PresencePath
    ]

if (
    $null -eq $Heartbeat
)
{
    throw (
        "Missing OpenAPI route: " +
        $HeartbeatPath
    )
}

if (
    $null -eq $Presence
)
{
    throw (
        "Missing OpenAPI route: " +
        $PresencePath
    )
}

if (
    $null -eq $Heartbeat.Value.post
)
{
    throw (
        "Heartbeat route exists but POST operation is missing."
    )
}

if (
    $null -eq $Presence.Value.get
)
{
    throw (
        "Presence route exists but GET operation is missing."
    )
}

Write-Host ""
Write-Host "Found:"
Write-Host "POST $HeartbeatPath"
Write-Host "GET  $PresencePath"

Write-Host ""
Write-Host "=============================================="
Write-Host " PHASE 07 BACKEND OPENAPI SMOKE: PASS"
Write-Host "=============================================="
Write-Host ""