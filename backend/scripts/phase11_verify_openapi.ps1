#Requires -Version 5.1

param(
    [string]$BackendBaseUrl = "http://127.0.0.1:8001"
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "==============================================="
Write-Host " WorkforceOS Phase 11 OpenAPI Verification"
Write-Host "==============================================="
Write-Host ""

$OpenApiUrl = "$BackendBaseUrl/openapi.json"

Write-Host ("Reading: " + $OpenApiUrl)

$OpenApi = Invoke-RestMethod `
    -Uri $OpenApiUrl `
    -Method Get

if ($null -eq $OpenApi)
{
    throw "OpenAPI response was empty."
}

if ($null -eq $OpenApi.paths)
{
    throw "OpenAPI response does not contain paths."
}

$Paths = $OpenApi.paths.PSObject.Properties.Name

$RequiredPaths = @(
    "/api/v1/device-agent/website-observation",
    "/api/v1/device-agent/website-status",
    "/api/v1/device-agent/website-history"
)

foreach ($RequiredPath in $RequiredPaths)
{
    if ($Paths -notcontains $RequiredPath)
    {
        Write-Host ""
        Write-Host "Available Website Tracking paths:"

        $Paths |
            Where-Object {
                $_ -like "*website*"
            } |
            Sort-Object |
            ForEach-Object {
                Write-Host (" - " + $_)
            }

        throw (
            "Required Phase 11 route missing: " +
            $RequiredPath
        )
    }

    Write-Host (
        "PASS route registered: " +
        $RequiredPath
    )
}

Write-Host ""

$ObservationProperty = $OpenApi.paths.PSObject.Properties[
    "/api/v1/device-agent/website-observation"
]

if ($null -eq $ObservationProperty)
{
    throw "Website observation path object missing."
}

$ObservationPath = $ObservationProperty.Value

if ($null -eq $ObservationPath.post)
{
    throw "Website observation POST operation missing."
}

Write-Host "PASS website observation POST"


$StatusProperty = $OpenApi.paths.PSObject.Properties[
    "/api/v1/device-agent/website-status"
]

if ($null -eq $StatusProperty)
{
    throw "Website status path object missing."
}

$StatusPath = $StatusProperty.Value

if ($null -eq $StatusPath.get)
{
    throw "Website status GET operation missing."
}

Write-Host "PASS website status GET"


$HistoryProperty = $OpenApi.paths.PSObject.Properties[
    "/api/v1/device-agent/website-history"
]

if ($null -eq $HistoryProperty)
{
    throw "Website history path object missing."
}

$HistoryPath = $HistoryProperty.Value

if ($null -eq $HistoryPath.get)
{
    throw "Website history GET operation missing."
}

Write-Host "PASS website history GET"

Write-Host ""
Write-Host "==============================================="
Write-Host " PHASE 11 OPENAPI: PASS"
Write-Host "==============================================="
Write-Host ""