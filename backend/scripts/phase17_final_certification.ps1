$ErrorActionPreference = "Stop"


$BackendRoot = "C:\workforce-os\backend"

$Python = Join-Path `
    $BackendRoot `
    ".venv\Scripts\python.exe"


Set-Location $BackendRoot


function Fail-Certification
{
    param(
        [Parameter(Mandatory = $true)]
        [string] $Message
    )

    Write-Host ""
    Write-Host "================================================="
    Write-Host " PHASE 17 FINAL CERTIFICATION: FAIL"
    Write-Host "================================================="
    Write-Host "ERROR:" $Message
    Write-Host "================================================="
    Write-Host ""

    exit 1
}


function Invoke-CertificationGate
{
    param(
        [Parameter(Mandatory = $true)]
        [string] $Path,

        [Parameter(Mandatory = $true)]
        [string] $Name
    )

    if (-not (Test-Path $Path))
    {
        Fail-Certification (
            "Missing certification gate: {0}" `
                -f $Path
        )
    }

    Write-Host ""
    Write-Host "-------------------------------------------------"
    Write-Host $Name
    Write-Host "-------------------------------------------------"

    & powershell.exe `
        -NoProfile `
        -ExecutionPolicy Bypass `
        -File $Path

    if ($LASTEXITCODE -ne 0)
    {
        Fail-Certification (
            "{0} failed with exit code {1}." `
                -f $Name, $LASTEXITCODE
        )
    }

    Write-Host "PASS $Name"
}


Write-Host "================================================="
Write-Host " WorkforceOS Phase 17 Final Certification"
Write-Host "================================================="
Write-Host ""


$RequiredFiles = @(
    ".\app\modules\channels\realtime_ticket.py",
    ".\app\modules\channels\realtime_websocket.py",
    ".\app\modules\channels\realtime_service.py",
    ".\app\modules\channels\realtime_presence.py",
    ".\app\modules\channels\realtime_pubsub.py",
    ".\app\modules\channels\realtime_replay.py",
    ".\app\modules\channels\read_state_repository.py",
    ".\app\modules\channels\hardening\config.py",
    ".\app\modules\channels\hardening\access.py",
    ".\app\modules\channels\hardening\rate_limit.py",
    ".\app\modules\channels\hardening\presence_guard.py",
    ".\app\modules\channels\hardening\read_state_upsert.py",
    ".\app\modules\channels\hardening\observability.py",
    ".\app\modules\attachments\service.py",
    ".\scripts\phase17_hardening_foundation_gate.ps1",
    ".\scripts\phase17_batch2_gate.ps1",
    ".\scripts\phase17_runtime_regression_gate.ps1",
    ".\scripts\phase17_production_config_gate.py",
    ".\scripts\phase17_security_regression_gate.ps1",
    ".\scripts\phase17_production_readiness_gate.ps1"
)


Write-Host "[1/5] Final required files..."


foreach ($File in $RequiredFiles)
{
    if (-not (Test-Path $File))
    {
        Fail-Certification (
            "Missing final required file: {0}" `
                -f $File
        )
    }
}


Write-Host "PASS final required files"
Write-Host ""


Write-Host "[2/5] Final compile..."


& $Python `
    -m compileall `
    ".\app" `
    ".\tests\channels" `
    ".\scripts\phase17_production_config_gate.py" `
    -q


if ($LASTEXITCODE -ne 0)
{
    Fail-Certification `
        "Final Python compile failed."
}


Write-Host "PASS final compile"
Write-Host ""


Write-Host "[3/5] Production readiness..."


Invoke-CertificationGate `
    -Path (
        Join-Path `
            $BackendRoot `
            "scripts\phase17_production_readiness_gate.ps1"
    ) `
    -Name "Production Readiness"


Write-Host ""
Write-Host "[4/5] Attachment lifecycle..."


& $Python `
    ".\scripts\phase17_attachment_access_contract.py"


if ($LASTEXITCODE -ne 0)
{
    Fail-Certification `
        "Attachment lifecycle certification failed."
}


Write-Host "PASS attachment lifecycle"
Write-Host ""


Write-Host "[5/5] Final security suite..."


& $Python `
    -m pytest `
    ".\tests\channels\test_phase17_realtime_security.py" `
    ".\tests\channels\test_phase17_ticket_atomicity.py" `
    ".\tests\channels\test_phase17_websocket_hardening.py" `
    ".\tests\channels\test_phase17_presence_hardening.py" `
    ".\tests\channels\test_phase17_replay_bounds.py" `
    ".\tests\channels\test_phase17_pubsub_lifecycle.py" `
    ".\tests\channels\test_phase17_access_readstate_contract.py" `
    -q


if ($LASTEXITCODE -ne 0)
{
    Fail-Certification `
        "Final Phase 17 security suite failed."
}


Write-Host "PASS final security suite"
Write-Host ""


Write-Host "================================================="
Write-Host " PHASE 17 PRODUCTION HARDENING: CERTIFIED / PASS"
Write-Host "================================================="
Write-Host "Batch 1 foundation:               PASS"
Write-Host "Atomic one-use tickets:           PASS"
Write-Host "Membership revalidation:          PASS"
Write-Host "Realtime rate limiting:           PASS"
Write-Host "Presence / typing expiry:         PASS"
Write-Host "Read-state atomic UPSERT:         PASS"
Write-Host "Attachment lifecycle access:      PASS"
Write-Host "Redis pubsub lifecycle:           PASS"
Write-Host "Reconnect / replay bounds:        PASS"
Write-Host "Runtime regression:               PASS"
Write-Host "Security regression:              PASS"
Write-Host "Production readiness:             PASS"
Write-Host "================================================="
Write-Host " PHASE 17 COMPLETION:              100%"
Write-Host " NEXT: PHASE 18 END-TO-END CERTIFICATION"
Write-Host "================================================="
Write-Host ""

exit 0