#Requires -Version 5.1

param(
    [string]$ChromeExtensionId = "",
    [string]$EdgeExtensionId = ""
)

$ErrorActionPreference = "Stop"

$HostName = "com.workforceos.website_tracking"

$NativeHostExe = (
    "C:\workforce-os\artifacts\website-native-host\" +
    "WorkforceOS.WebsiteNativeHost.exe"
)

$ManifestDirectory = (
    "C:\workforce-os\artifacts\website-native-host\native-host"
)

$ManifestPath = Join-Path `
    $ManifestDirectory `
    ($HostName + ".json")

if (-not (Test-Path $NativeHostExe))
{
    throw (
        "Native host executable not found: " +
        $NativeHostExe
    )
}

$Origins = @()

if (-not [string]::IsNullOrWhiteSpace($ChromeExtensionId))
{
    if ($ChromeExtensionId -notmatch "^[a-p]{32}$")
    {
        throw "Chrome extension ID is invalid."
    }

    $Origins += (
        "chrome-extension://" +
        $ChromeExtensionId +
        "/"
    )
}

if (-not [string]::IsNullOrWhiteSpace($EdgeExtensionId))
{
    if ($EdgeExtensionId -notmatch "^[a-p]{32}$")
    {
        throw "Edge extension ID is invalid."
    }

    $EdgeOrigin = (
        "chrome-extension://" +
        $EdgeExtensionId +
        "/"
    )

    if ($Origins -notcontains $EdgeOrigin)
    {
        $Origins += $EdgeOrigin
    }
}

if ($Origins.Count -eq 0)
{
    throw (
        "At least one Chrome or Edge extension ID is required."
    )
}

New-Item `
    -ItemType Directory `
    -Path $ManifestDirectory `
    -Force |
Out-Null

$Manifest = [ordered]@{
    name = $HostName
    description = "WorkforceOS disclosed website tracking native messaging host"
    path = $NativeHostExe
    type = "stdio"
    allowed_origins = $Origins
}

$Manifest |
    ConvertTo-Json `
        -Depth 5 |
    Set-Content `
        -Path $ManifestPath `
        -Encoding UTF8

$ChromeRegistry = (
    "HKCU:\Software\Google\Chrome\NativeMessagingHosts\" +
    $HostName
)

$EdgeRegistry = (
    "HKCU:\Software\Microsoft\Edge\NativeMessagingHosts\" +
    $HostName
)

New-Item `
    -Path $ChromeRegistry `
    -Force |
Out-Null

Set-Item `
    -Path $ChromeRegistry `
    -Value $ManifestPath

New-Item `
    -Path $EdgeRegistry `
    -Force |
Out-Null

Set-Item `
    -Path $EdgeRegistry `
    -Value $ManifestPath

Write-Host ""
Write-Host "Native host manifest:"
Write-Host $ManifestPath
Write-Host ""

Write-Host "Allowed origins:"

foreach ($Origin in $Origins)
{
    Write-Host (" - " + $Origin)
}

Write-Host ""
Write-Host "PASS Chrome registration"
Write-Host "PASS Edge registration"

Write-Host ""
Write-Host "==============================================="
Write-Host " PHASE 11 BROWSER HOST REGISTRATION: PASS"
Write-Host "==============================================="
Write-Host ""