#Requires -RunAsAdministrator
#Requires -Version 5.1

$ErrorActionPreference =
    "Stop"

$ServiceName =
    "WorkforceOSAgent"

$PublishedExecutable =
    "C:\workforce-os\artifacts\agent\win-x64\WorkforceOS.Agent.exe"

$WaitAfterRestartSeconds =
    8

$HeartbeatObservationSeconds =
    40

Write-Host ""
Write-Host "============================================"
Write-Host " WorkforceOS Phase 07 Live Heartbeat Smoke"
Write-Host "============================================"
Write-Host ""

if (
    -not (
        Test-Path $PublishedExecutable
    )
)
{
    throw (
        "Published agent not found: " +
        $PublishedExecutable
    )
}

$Service =
    Get-Service `
        -Name $ServiceName `
        -ErrorAction Stop

Write-Host "Service:"
Write-Host $Service.Name
Write-Host ""

Write-Host "Restarting WorkforceOS Agent service..."

Restart-Service `
    -Name $ServiceName `
    -Force

Start-Sleep `
    -Seconds $WaitAfterRestartSeconds

$Service =
    Get-Service `
        -Name $ServiceName

if (
    $Service.Status
    -ne "Running"
)
{
    throw (
        "WorkforceOS Agent service is not running."
    )
}

Write-Host "Service is running."
Write-Host ""

Write-Host "Waiting for first heartbeat..."

Start-Sleep `
    -Seconds 5

Write-Host ""
Write-Host "Checking backend presence..."

$FirstPresence =
    & $PublishedExecutable `
        --presence `
        2>&1

$FirstExitCode =
    $LASTEXITCODE

$FirstPresenceText =
    (
        $FirstPresence |
        Out-String
    )

Write-Host $FirstPresenceText.Trim()

if (
    $FirstExitCode -ne 0
)
{
    throw (
        "First presence check failed."
    )
}

if (
    -not $FirstPresenceText.Contains(
        "Online: True"
    )
)
{
    throw (
        "Device was not reported online after service start."
    )
}

if (
    -not $FirstPresenceText.Contains(
        "Last Seen:"
    )
)
{
    throw (
        "Presence response does not include Last Seen."
    )
}

Write-Host ""
Write-Host (
    "Waiting " +
    $HeartbeatObservationSeconds +
    " seconds for another heartbeat..."
)

Start-Sleep `
    -Seconds $HeartbeatObservationSeconds

Write-Host ""
Write-Host "Checking presence again..."

$SecondPresence =
    & $PublishedExecutable `
        --presence `
        2>&1

$SecondExitCode =
    $LASTEXITCODE

$SecondPresenceText =
    (
        $SecondPresence |
        Out-String
    )

Write-Host $SecondPresenceText.Trim()

if (
    $SecondExitCode -ne 0
)
{
    throw (
        "Second presence check failed."
    )
}

if (
    -not $SecondPresenceText.Contains(
        "Online: True"
    )
)
{
    throw (
        "Device did not remain online across heartbeat interval."
    )
}

$Service =
    Get-Service `
        -Name $ServiceName

if (
    $Service.Status
    -ne "Running"
)
{
    throw (
        "Service stopped during heartbeat observation."
    )
}

Write-Host ""
Write-Host "============================================"
Write-Host " PHASE 07 LIVE HEARTBEAT SMOKE: PASS"
Write-Host "============================================"
Write-Host ""