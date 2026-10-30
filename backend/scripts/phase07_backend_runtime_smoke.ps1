$ErrorActionPreference = "Stop"

$BaseUrl =
    "http://127.0.0.1:8001"

$OpenApiUrl =
    "$BaseUrl/openapi.json"

Write-Host ""
Write-Host "============================================="
Write-Host " WorkforceOS Phase 07 Backend Runtime Smoke"
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

if (
    $null -eq $Schema.paths
)
{
    throw (
        "OpenAPI response does not contain paths."
    )
}

$HeartbeatPath =
    "/api/v1/device-agent/heartbeat"

$PresencePath =
    "/api/v1/device-agent/presence"

$HeartbeatProperty =
    $Schema.paths.PSObject.Properties[
        $HeartbeatPath
    ]

$PresenceProperty =
    $Schema.paths.PSObject.Properties[
        $PresencePath
    ]

if (
    $null -eq $HeartbeatProperty
)
{
    throw (
        "Heartbeat route is not mounted."
    )
}

if (
    $null -eq $PresenceProperty
)
{
    throw (
        "Presence route is not mounted."
    )
}

if (
    $null -eq $HeartbeatProperty.Value.post
)
{
    throw (
        "POST heartbeat operation is missing."
    )
}

if (
    $null -eq $PresenceProperty.Value.get
)
{
    throw (
        "GET presence operation is missing."
    )
}

Write-Host (
    "PASS POST " +
    $HeartbeatPath
)

Write-Host (
    "PASS GET  " +
    $PresencePath
)

Write-Host ""
Write-Host "============================================="
Write-Host " PHASE 07 BACKEND RUNTIME SMOKE: PASS"
Write-Host "============================================="
Write-Host ""