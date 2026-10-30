#Requires -Version 5.1

$ErrorActionPreference = "Stop"

$ServiceName = "WorkforceOSAgent"

Write-Host ""
Write-Host "==============================================="
Write-Host " WorkforceOS Agent Restart"
Write-Host "==============================================="
Write-Host ""

$Service = Get-Service `
    -Name $ServiceName `
    -ErrorAction Stop

if ($Service.Status -eq "Running")
{
    Write-Host "Stopping Agent service..."

    Stop-Service `
        -Name $ServiceName `
        -Force

    $Service.WaitForStatus(
        "Stopped",
        [TimeSpan]::FromSeconds(30)
    )
}

Write-Host "Starting Agent service..."

Start-Service `
    -Name $ServiceName

$Service = Get-Service `
    -Name $ServiceName

$Service.WaitForStatus(
    "Running",
    [TimeSpan]::FromSeconds(30)
)

$Service = Get-Service `
    -Name $ServiceName

if ($Service.Status -ne "Running")
{
    throw "WorkforceOS Agent service failed to start."
}

Write-Host ""
Write-Host "Service:"
Write-Host ("Name   : " + $Service.Name)
Write-Host ("Status : " + $Service.Status)

Write-Host ""
Write-Host "==============================================="
Write-Host " PHASE 11 AGENT RESTART: PASS"
Write-Host "==============================================="
Write-Host ""