#Requires -RunAsAdministrator
#Requires -Version 5.1

$ErrorActionPreference = "Stop"

$ServiceName = "WorkforceOSAgent"

$PublishedExecutable =
    "C:\workforce-os\artifacts\agent\win-x64\WorkforceOS.Agent.exe"

$OnlineTimeoutSeconds = 90
$SafetyMarginSeconds = 10
$OfflineWaitSeconds = $OnlineTimeoutSeconds + $SafetyMarginSeconds

Write-Host ""
Write-Host "================================================"
Write-Host " WorkforceOS Phase 07 Offline Timeout Smoke"
Write-Host "================================================"
Write-Host ""

# =========================================================
# VALIDATE EXECUTABLE
# =========================================================

if (-not (Test-Path $PublishedExecutable))
{
    throw (
        "Published WorkforceOS Agent executable not found: " +
        $PublishedExecutable
    )
}

# =========================================================
# ENSURE SERVICE IS RUNNING
# =========================================================

$Service =
    Get-Service `
        -Name $ServiceName `
        -ErrorAction Stop

if ($Service.Status -ne "Running")
{
    Write-Host "Starting WorkforceOS Agent service..."

    Start-Service `
        -Name $ServiceName `
        -ErrorAction Stop

    $Service =
        Get-Service `
            -Name $ServiceName `
            -ErrorAction Stop

    $Service.WaitForStatus(
        "Running",
        [TimeSpan]::FromSeconds(20)
    )

    Start-Sleep -Seconds 8
}

$Service =
    Get-Service `
        -Name $ServiceName `
        -ErrorAction Stop

if ($Service.Status -ne "Running")
{
    throw "WorkforceOS Agent service is not running."
}

# =========================================================
# INITIAL ONLINE CHECK
# =========================================================

Write-Host ""
Write-Host "Checking initial online state..."

$OnlineOutput =
    & $PublishedExecutable `
        --presence `
        2>&1

$OnlineExitCode =
    $LASTEXITCODE

$OnlineText =
    $OnlineOutput |
    Out-String

Write-Host ""
Write-Host $OnlineText.Trim()

if ($OnlineExitCode -ne 0)
{
    throw (
        "Initial presence request failed:`n" +
        $OnlineText
    )
}

if (-not $OnlineText.Contains("Online: True"))
{
    throw (
        "Device must be online before offline timeout test starts.`n" +
        $OnlineText
    )
}

# =========================================================
# STOP SERVICE
# =========================================================

Write-Host ""
Write-Host "Stopping WorkforceOS Agent service..."

Stop-Service `
    -Name $ServiceName `
    -Force `
    -ErrorAction Stop

$Service =
    Get-Service `
        -Name $ServiceName `
        -ErrorAction Stop

$Service.WaitForStatus(
    "Stopped",
    [TimeSpan]::FromSeconds(20)
)

$Service =
    Get-Service `
        -Name $ServiceName `
        -ErrorAction Stop

if ($Service.Status -ne "Stopped")
{
    throw "Unable to stop WorkforceOS Agent service."
}

Write-Host "Service stopped."

# =========================================================
# WAIT FOR OFFLINE TIMEOUT
# =========================================================

Write-Host ""
Write-Host (
    "Waiting " +
    $OfflineWaitSeconds +
    " seconds for heartbeat timeout..."
)

Start-Sleep `
    -Seconds $OfflineWaitSeconds

# =========================================================
# OFFLINE CHECK
# =========================================================

Write-Host ""
Write-Host "Checking offline presence..."

$OfflineOutput =
    & $PublishedExecutable `
        --presence `
        2>&1

$OfflineExitCode =
    $LASTEXITCODE

$OfflineText =
    $OfflineOutput |
    Out-String

Write-Host ""
Write-Host $OfflineText.Trim()

if ($OfflineExitCode -ne 0)
{
    throw (
        "Offline presence request failed:`n" +
        $OfflineText
    )
}

if (-not $OfflineText.Contains("Online: False"))
{
    throw (
        "Device was expected to be offline after heartbeat timeout.`n" +
        $OfflineText
    )
}

if (-not $OfflineText.Contains("Offline Since:"))
{
    throw (
        "Offline response does not contain Offline Since timestamp.`n" +
        $OfflineText
    )
}

Write-Host ""
Write-Host "Offline timeout confirmed."

# =========================================================
# RESTART SERVICE
# =========================================================

Write-Host ""
Write-Host "Restarting WorkforceOS Agent service..."

Start-Service `
    -Name $ServiceName `
    -ErrorAction Stop

$Service =
    Get-Service `
        -Name $ServiceName `
        -ErrorAction Stop

$Service.WaitForStatus(
    "Running",
    [TimeSpan]::FromSeconds(20)
)

$Service =
    Get-Service `
        -Name $ServiceName `
        -ErrorAction Stop

if ($Service.Status -ne "Running")
{
    throw (
        "WorkforceOS Agent failed to restart after offline timeout test."
    )
}

# =========================================================
# RECOVERY WAIT
# =========================================================

Write-Host ""
Write-Host "Waiting for recovery heartbeat..."

Start-Sleep -Seconds 10

# =========================================================
# ONLINE RECOVERY CHECK
# =========================================================

Write-Host ""
Write-Host "Checking online recovery..."

$RecoveryOutput =
    & $PublishedExecutable `
        --presence `
        2>&1

$RecoveryExitCode =
    $LASTEXITCODE

$RecoveryText =
    $RecoveryOutput |
    Out-String

Write-Host ""
Write-Host $RecoveryText.Trim()

if ($RecoveryExitCode -ne 0)
{
    throw (
        "Recovery presence request failed:`n" +
        $RecoveryText
    )
}

if (-not $RecoveryText.Contains("Online: True"))
{
    throw (
        "Device did not return online after service restart.`n" +
        $RecoveryText
    )
}

# =========================================================
# FINAL SERVICE CHECK
# =========================================================

$Service =
    Get-Service `
        -Name $ServiceName `
        -ErrorAction Stop

if ($Service.Status -ne "Running")
{
    throw (
        "WorkforceOS Agent service is not running after recovery validation."
    )
}

Write-Host ""
Write-Host "================================================"
Write-Host " PHASE 07 OFFLINE TIMEOUT SMOKE: PASS"
Write-Host "================================================"
Write-Host ""