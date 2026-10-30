$ErrorActionPreference = "Stop"


$BackendRoot = "C:\workforce-os\backend"

$Python = Join-Path `
    $BackendRoot `
    ".venv\Scripts\python.exe"


Set-Location $BackendRoot


function Fail-Gate
{
    param(
        [Parameter(Mandatory = $true)]
        [string] $Message
    )

    Write-Host ""
    Write-Host "================================================="
    Write-Host " PHASE 17 SECURITY REGRESSION: FAIL"
    Write-Host "================================================="
    Write-Host "ERROR:" $Message
    Write-Host "================================================="

    exit 1
}


Write-Host "================================================="
Write-Host " WorkforceOS Phase 17 Security Regression"
Write-Host "================================================="
Write-Host ""


$Tests = @(
    ".\tests\channels\test_phase17_realtime_security.py",
    ".\tests\channels\test_phase17_ticket_atomicity.py",
    ".\tests\channels\test_phase17_websocket_hardening.py",
    ".\tests\channels\test_phase17_presence_hardening.py",
    ".\tests\channels\test_phase17_replay_bounds.py",
    ".\tests\channels\test_phase17_pubsub_lifecycle.py",
    ".\tests\channels\test_phase17_access_readstate_contract.py"
)


Write-Host "[1/4] Required tests..."


foreach ($Test in $Tests)
{
    if (-not (Test-Path $Test))
    {
        Fail-Gate (
            "Missing security test: {0}" `
                -f $Test
        )
    }
}


Write-Host "PASS required tests"
Write-Host ""


Write-Host "[2/4] Compiling security tests..."


& $Python `
    -m compileall `
    ".\tests\channels" `
    -q


if ($LASTEXITCODE -ne 0)
{
    Fail-Gate `
        "Security test compile failed."
}


Write-Host "PASS security test compile"
Write-Host ""


Write-Host "[3/4] Production config..."


& $Python `
    ".\scripts\phase17_production_config_gate.py"


if ($LASTEXITCODE -ne 0)
{
    Fail-Gate `
        "Production configuration gate failed."
}


Write-Host "PASS production configuration"
Write-Host ""


Write-Host "[4/4] Realtime security suite..."


& $Python `
    -m pytest `
    $Tests `
    -q


if ($LASTEXITCODE -ne 0)
{
    Fail-Gate `
        "Realtime security regression failed."
}


Write-Host "PASS realtime security suite"
Write-Host ""


Write-Host "================================================="
Write-Host " PHASE 17 SECURITY REGRESSION: PASS"
Write-Host "================================================="
Write-Host "Test inventory:                   PASS"
Write-Host "Compile:                          PASS"
Write-Host "Production config:                PASS"
Write-Host "Realtime security suite:          PASS"
Write-Host "================================================="

exit 0