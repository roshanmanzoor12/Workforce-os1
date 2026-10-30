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

if (Test-Path $ChromeRegistry)
{
    Remove-Item `
        -Path $ChromeRegistry `
        -Recurse `
        -Force

    Write-Host "Removed Chrome native host registration"
}

if (Test-Path $EdgeRegistry)
{
    Remove-Item `
        -Path $EdgeRegistry `
        -Recurse `
        -Force

    Write-Host "Removed Edge native host registration"
}

Write-Host ""
Write-Host "PASS Phase 11 browser host unregister"