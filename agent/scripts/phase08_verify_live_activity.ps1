#Requires -Version 5.1

$ErrorActionPreference = "Stop"

$PublishedExecutable =
    "C:\workforce-os\artifacts\agent\win-x64\WorkforceOS.Agent.exe"

$ServiceName =
    "WorkforceOSAgent"

$BackendBaseUrl =
    "http://127.0.0.1:8001"

$ActivityStatusUrl =
    "$BackendBaseUrl/api/v1/device-agent/activity-status"

$HelperRunSeconds =
    45

Write-Host ""
Write-Host "================================================="
Write-Host " WorkforceOS Phase 08 Live Activity Verification"
Write-Host "================================================="
Write-Host ""

# ============================================================
# 1. VERIFY PUBLISHED AGENT
# ============================================================

Write-Host "[1/5] Verifying published agent..."

if (-not (Test-Path $PublishedExecutable))
{
    throw (
        "Published WorkforceOS Agent not found: " +
        $PublishedExecutable
    )
}

Write-Host "PASS published agent exists"
Write-Host ""

# ============================================================
# 2. VERIFY WINDOWS SERVICE
# ============================================================

Write-Host "[2/5] Verifying WorkforceOS service..."

$Service =
    Get-Service `
        -Name $ServiceName `
        -ErrorAction SilentlyContinue

if ($null -eq $Service)
{
    throw (
        "Windows service not found: " +
        $ServiceName
    )
}

if ($Service.Status -ne "Running")
{
    throw (
        "WorkforceOS service is not running. Current status: " +
        $Service.Status
    )
}

Write-Host "PASS WorkforceOS service running"
Write-Host ""

# ============================================================
# 3. START INTERACTIVE HELPER
# ============================================================

Write-Host "[3/5] Starting activity session helper..."

$HelperProcess =
    Start-Process `
        -FilePath $PublishedExecutable `
        -ArgumentList "--activity-session-helper" `
        -PassThru

if ($null -eq $HelperProcess)
{
    throw (
        "Unable to start WorkforceOS activity session helper."
    )
}

Write-Host (
    "Helper started with PID " +
    $HelperProcess.Id
)

Write-Host (
    "Waiting " +
    $HelperRunSeconds +
    " seconds for activity observation..."
)

Start-Sleep `
    -Seconds $HelperRunSeconds

$HelperProcess.Refresh()

if ($HelperProcess.HasExited)
{
    throw (
        "Activity session helper exited unexpectedly with code " +
        $HelperProcess.ExitCode
    )
}

Write-Host "PASS helper remained running"
Write-Host ""

# ============================================================
# 4. STOP HELPER
# ============================================================

Write-Host "[4/5] Stopping activity session helper..."

Stop-Process `
    -Id $HelperProcess.Id `
    -Force

Start-Sleep `
    -Seconds 2

$StoppedProcess =
    Get-Process `
        -Id $HelperProcess.Id `
        -ErrorAction SilentlyContinue

if ($null -ne $StoppedProcess)
{
    throw (
        "Activity helper process did not stop."
    )
}

Write-Host "PASS helper stopped"
Write-Host ""

# ============================================================
# 5. NEXT AUTHENTICATED BACKEND VERIFICATION
# ============================================================

Write-Host "[5/5] Live observation stage complete."
Write-Host ""
Write-Host "The helper ran inside the current interactive user session"
Write-Host "and had time to send an activity observation to the service."
Write-Host ""
Write-Host "Next verification:"
Write-Host "confirm the latest activity event in the tenant database"
Write-Host "or query the authenticated activity-status endpoint."
Write-Host ""

Write-Host "================================================="
Write-Host " PHASE 08 LIVE HELPER VERIFICATION: PASS"
Write-Host "================================================="
Write-Host ""