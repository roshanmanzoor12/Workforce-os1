#Requires -Version 5.1

$ErrorActionPreference = "Stop"

$BaseUrl = "http://127.0.0.1:8001"
$OpenApiUrl = "$BaseUrl/openapi.json"

$ActivityStatePath = "/api/v1/device-agent/activity-state"
$ActivityStatusPath = "/api/v1/device-agent/activity-status"

Write-Host ""
Write-Host "================================================"
Write-Host " WorkforceOS Phase 08 Runtime Contract Smoke"
Write-Host "================================================"
Write-Host ""

# ============================================================
# 1. BACKEND HEALTH
# ============================================================

Write-Host "[1/4] Checking backend..."

try
{
    $Root = Invoke-RestMethod `
        -Method Get `
        -Uri "$BaseUrl/" `
        -TimeoutSec 10
}
catch
{
    throw "WorkforceOS backend is not reachable at $BaseUrl"
}

if ($Root.status -ne "running")
{
    throw "Unexpected backend root status: $($Root.status)"
}

Write-Host "PASS backend running"
Write-Host ""

# ============================================================
# 2. OPENAPI
# ============================================================

Write-Host "[2/4] Loading OpenAPI..."

try
{
    $Schema = Invoke-RestMethod `
        -Method Get `
        -Uri $OpenApiUrl `
        -TimeoutSec 10
}
catch
{
    throw "Unable to load WorkforceOS OpenAPI schema from $OpenApiUrl"
}

if ($null -eq $Schema.paths)
{
    throw "OpenAPI schema does not contain paths."
}

Write-Host "PASS OpenAPI available"
Write-Host ""

# ============================================================
# 3. ACTIVITY ROUTES
# ============================================================

Write-Host "[3/4] Checking activity routes..."

$StateRoute = $Schema.paths.PSObject.Properties[$ActivityStatePath]
$StatusRoute = $Schema.paths.PSObject.Properties[$ActivityStatusPath]

if ($null -eq $StateRoute)
{
    throw "Missing runtime route: $ActivityStatePath"
}

if ($null -eq $StatusRoute)
{
    throw "Missing runtime route: $ActivityStatusPath"
}

if ($null -eq $StateRoute.Value.post)
{
    throw "POST operation missing from activity-state route."
}

if ($null -eq $StatusRoute.Value.get)
{
    throw "GET operation missing from activity-status route."
}

Write-Host "PASS POST $ActivityStatePath"
Write-Host "PASS GET  $ActivityStatusPath"
Write-Host ""

# ============================================================
# 4. AUTHENTICATION PROTECTION
# ============================================================

Write-Host "[4/4] Checking device authentication protection..."

$UnauthenticatedStatusCode = $null

try
{
    $Response = Invoke-WebRequest `
        -Method Get `
        -Uri "$BaseUrl$ActivityStatusPath" `
        -UseBasicParsing `
        -TimeoutSec 10

    $UnauthenticatedStatusCode = [int]$Response.StatusCode
}
catch
{
    if ($null -ne $_.Exception.Response)
    {
        $UnauthenticatedStatusCode = [int]$_.Exception.Response.StatusCode
    }
    else
    {
        throw
    }
}

if ($null -eq $UnauthenticatedStatusCode)
{
    throw "Unable to determine unauthenticated activity-status response."
}

if ($UnauthenticatedStatusCode -eq 200)
{
    throw "Unauthenticated activity-status request was unexpectedly accepted."
}

$AcceptedUnauthenticatedStatuses =
    @(
        401,
        403,
        422
    )

if ($AcceptedUnauthenticatedStatuses -notcontains $UnauthenticatedStatusCode)
{
    throw (
        "Expected HTTP 401, 403, or 422 from unauthenticated " +
        "activity-status request, received HTTP $UnauthenticatedStatusCode"
    )
}

if ($UnauthenticatedStatusCode -eq 422)
{
    Write-Host (
        "PASS unauthenticated request rejected with HTTP 422 " +
        "(required device authentication headers are missing)"
    )
}
else
{
    Write-Host (
        "PASS unauthenticated request rejected with HTTP " +
        $UnauthenticatedStatusCode
    )
}

Write-Host ""
Write-Host "================================================"
Write-Host " PHASE 08 RUNTIME CONTRACT SMOKE: PASS"
Write-Host "================================================"
Write-Host ""