$ErrorActionPreference = "Stop"

$BackendRoot = "C:\workforce-os\backend"
$Python = "C:\workforce-os\backend\.venv\Scripts\python.exe"

Set-Location $BackendRoot

Write-Host "================================================="
Write-Host " WorkforceOS Phase 11.8 Regression Gate"
Write-Host "================================================="
Write-Host ""

Write-Host "[1/4] Compile..."

& $Python `
    -m compileall `
    .\app\modules\workspace_permissions `
    .\app\modules\meetings `
    .\app\modules\monitoring_control `
    .\app\modules\tenant_api `
    -q

if (
    $LASTEXITCODE -ne 0
)
{
    throw "Phase 11.8 compile failed."
}

Write-Host "PASS compile"
Write-Host ""

Write-Host "[2/4] Permission + meetings tests..."

& $Python `
    -m pytest `
    .\tests\test_phase11_8_workspace_permissions.py `
    .\tests\test_phase11_8_meetings_foundation.py `
    .\tests\test_phase11_8_meeting_lifecycle_contract.py `
    -q

if (
    $LASTEXITCODE -ne 0
)
{
    throw "Meetings regression failed."
}

Write-Host "PASS meetings"
Write-Host ""

Write-Host "[3/4] Monitoring tests..."

& $Python `
    -m pytest `
    .\tests\test_phase11_8_meeting_self_and_monitoring.py `
    .\tests\test_phase11_8_monitoring_control_contract.py `
    -q

if (
    $LASTEXITCODE -ne 0
)
{
    throw "Monitoring regression failed."
}

Write-Host "PASS monitoring"
Write-Host ""

Write-Host "[4/4] Security + routing..."

& $Python `
    -m pytest `
    .\tests\test_phase11_8_integration_contract.py `
    .\tests\test_phase11_8_router_order_contract.py `
    .\tests\test_phase11_8_security_regression.py `
    -q

if (
    $LASTEXITCODE -ne 0
)
{
    throw "Phase 11.8 security regression failed."
}

Write-Host "PASS security"
Write-Host ""

Write-Host "================================================="
Write-Host " PHASE 11.8 REGRESSION: PASS"
Write-Host "================================================="