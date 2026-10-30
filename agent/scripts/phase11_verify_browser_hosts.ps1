#Requires -Version 5.1

$ErrorActionPreference = "Stop"

$HostName = "com.workforceos.website_tracking"

$ChromeRegistry = (
    "HKCU:\Software\Google\Chrome\NativeMessagingHosts\" +
    $HostName
)

$EdgeRegistry = (
    "HKCU:\Software\Microsoft\Edge\NativeMessagingHosts\" +
    $HostName
)

Write-Host ""
Write-Host "==============================================="
Write-Host " WorkforceOS Browser Host Verification"
Write-Host "==============================================="
Write-Host ""

if (-not (Test-Path $ChromeRegistry))
{
    throw "Chrome native messaging registration missing."
}

if (-not (Test-Path $EdgeRegistry))
{
    throw "Edge native messaging registration missing."
}

$ChromeManifestPath = (
    Get-Item $ChromeRegistry
).GetValue("")

$EdgeManifestPath = (
    Get-Item $EdgeRegistry
).GetValue("")

if ([string]::IsNullOrWhiteSpace($ChromeManifestPath))
{
    throw "Chrome manifest path is empty."
}

if ([string]::IsNullOrWhiteSpace($EdgeManifestPath))
{
    throw "Edge manifest path is empty."
}

if ($ChromeManifestPath -ne $EdgeManifestPath)
{
    throw "Chrome and Edge registrations point to different manifests."
}

if (-not (Test-Path $ChromeManifestPath))
{
    throw (
        "Native messaging manifest missing: " +
        $ChromeManifestPath
    )
}

$Manifest = Get-Content `
    $ChromeManifestPath `
    -Raw |
ConvertFrom-Json

if ($Manifest.name -ne $HostName)
{
    throw "Native host manifest name is incorrect."
}

if (-not (Test-Path $Manifest.path))
{
    throw (
        "Native host executable missing: " +
        $Manifest.path
    )
}

if ($null -eq $Manifest.allowed_origins)
{
    throw "Native host allowed_origins missing."
}

if ($Manifest.allowed_origins.Count -lt 1)
{
    throw "Native host allowed_origins is empty."
}

Write-Host "PASS Chrome registry"
Write-Host "PASS Edge registry"
Write-Host "PASS manifest"
Write-Host "PASS native host executable"
Write-Host "PASS allowed origins"

Write-Host ""
Write-Host "Manifest:"
Write-Host $ChromeManifestPath

Write-Host ""
Write-Host "==============================================="
Write-Host " PHASE 11 BROWSER HOST VERIFY: PASS"
Write-Host "==============================================="
Write-Host ""