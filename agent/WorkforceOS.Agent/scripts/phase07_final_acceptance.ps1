#Requires -RunAsAdministrator
#Requires -Version 5.1

$ErrorActionPreference =
    "Stop"

$AgentScripts =
    $PSScriptRoot

$BackendRuntimeSmoke =
    "C:\workforce-os\backend\scripts\phase07_backend_runtime_smoke.ps1"

$PublishRestart =
    Join-Path `
        $AgentScripts `
        "phase07_publish_and_restart.ps1"

$LastSeenSmoke =
    Join-Path `
        $AgentScripts `
        "phase07_last_seen_progress_smoke.ps1"

$OfflineSmoke =
    Join-Path `
        $AgentScripts `
        "phase07_offline_timeout_smoke.ps1"

Write-Host ""
Write-Host "================================================"
Write-Host " WorkforceOS Phase 07 Final Acceptance"
Write-Host "================================================"
Write-Host ""

$RequiredScripts =
    @(
        $BackendRuntimeSmoke,
        $PublishRestart,
        $LastSeenSmoke,
        $OfflineSmoke
    )

foreach (
    $Script
    in $RequiredScripts
)
{
    if (
        -not (
            Test-Path $Script
        )
    )
    {
        throw (
            "Required Phase 07 script missing: " +
            $Script
        )
    }
}

Write-Host ""
Write-Host "[1/4] Backend runtime routes"
Write-Host ""

& $BackendRuntimeSmoke

if (
    $LASTEXITCODE -ne 0
)
{
    throw (
        "Backend runtime smoke failed."
    )
}

Write-Host ""
Write-Host "[2/4] Publish and restart agent"
Write-Host ""

& $PublishRestart

if (
    $LASTEXITCODE -ne 0
)
{
    throw (
        "Agent publish/restart failed."
    )
}

Write-Host ""
Write-Host "Waiting for initial heartbeat..."

Start-Sleep `
    -Seconds 8

Write-Host ""
Write-Host "[3/4] Recurring heartbeat validation"
Write-Host ""

& $LastSeenSmoke

if (
    $LASTEXITCODE -ne 0
)
{
    throw (
        "Last Seen progression smoke failed."
    )
}

Write-Host ""
Write-Host "[4/4] Offline timeout + recovery"
Write-Host ""

& $OfflineSmoke

if (
    $LASTEXITCODE -ne 0
)
{
    throw (
        "Offline timeout smoke failed."
    )
}

Write-Host ""
Write-Host "================================================"
Write-Host " WORKFORCEOS PHASE 07: ACCEPTANCE PASS"
Write-Host "================================================"
Write-Host ""
Write-Host "Validated:"
Write-Host " - heartbeat API mounted"
Write-Host " - presence API mounted"
Write-Host " - Windows service running"
Write-Host " - recurring heartbeat active"
Write-Host " - last_seen_at advances"
Write-Host " - device becomes offline after timeout"
Write-Host " - device returns online after service recovery"
Write-Host ""