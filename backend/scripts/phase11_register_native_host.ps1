#Requires -Version 5.1

param(
    [Parameter(Mandatory = $true)]
    [string]$ExtensionId
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($ExtensionId))
{
    throw "ExtensionId is required."
}

if ($ExtensionId -notmatch "^[a-p]{32}$")
{
    throw "ExtensionId must be a 32-character Chromium extension ID."
}

$HostName = "com.workforceos.website_tracking"

$ArtifactsDirectory = "C:\workforce-os\artifacts\website-native-host"

$LauncherPath = Join-Path `
    $ArtifactsDirectory `
    "WorkforceOS.WebsiteNativeHost.exe"

if (-not (Test-Path $LauncherPath))
{
    throw (
        "Native host launcher not found: " +
        $LauncherPath
    )
}

$ManifestDirectory = Join-Path `
    $ArtifactsDirectory `
    "native-host"

New-Item `
    -ItemType Directory `
    -Path $ManifestDirectory `
    -Force |
    Out-Null

$ManifestPath = Join-Path `
    $ManifestDirectory `
    ($HostName + ".json")

$Origin = (
    "chrome-extension://" +
    $ExtensionId +
    "/"
)

$ManifestObject = [ordered]@{
    name = $HostName
    description = "WorkforceOS disclosed website tracking native messaging host"
    path = $LauncherPath
    type = "stdio"
    allowed_origins = @(
        $Origin
    )
}

$ManifestJson = $ManifestObject |
    ConvertTo-Json `
        -Depth 5

Set-Content `
    -Path $ManifestPath `
    -Value $ManifestJson `
    -Encoding UTF8

Write-Host ""
Write-Host "Manifest created:"
Write-Host $ManifestPath
Write-Host ""

$ChromeKey = (
    "HKCU:\Software\Google\Chrome\NativeMessagingHosts\" +
    $HostName
)

$EdgeKey = (
    "HKCU:\Software\Microsoft\Edge\NativeMessagingHosts\" +
    $HostName
)

New-Item `
    -Path $ChromeKey `
    -Force |
    Out-Null

Set-Item `
    -Path $ChromeKey `
    -Value $ManifestPath

Write-Host "PASS Chrome native host registered"

New-Item `
    -Path $EdgeKey `
    -Force |
    Out-Null

Set-Item `
    -Path $EdgeKey `
    -Value $ManifestPath

Write-Host "PASS Edge native host registered"

Write-Host ""
Write-Host "Allowed extension origin:"
Write-Host $Origin

Write-Host ""
Write-Host "==============================================="
Write-Host " PHASE 11 NATIVE HOST REGISTRATION: PASS"
Write-Host "==============================================="
Write-Host ""