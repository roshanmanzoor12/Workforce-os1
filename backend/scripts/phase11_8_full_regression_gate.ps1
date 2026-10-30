$ErrorActionPreference = "Stop"

$BackendRoot = "C:\workforce-os\backend"
$Python = "C:\workforce-os\backend\.venv\Scripts\python.exe"

Set-Location $BackendRoot

Write-Host "================================================="
Write-Host " WorkforceOS Phase 11.8 Full Regression"
Write-Host "================================================="
Write-Host ""

Write-Host "[1/5] Compile..."

& $Python `
    -m compileall `
    .\app\modules\workspace_permissions `
    .\app\modules\meetings `
    .\app\modules\monitoring_control `
    .\app\modules\tenant_api `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Compile failed."
}

Write-Host "PASS compile"
Write-Host ""

Write-Host "[2/5] Permission tests..."

& $Python `
    -m pytest `
    .\tests\test_phase11_8_workspace_permissions.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Permission regression failed."
}

Write-Host "PASS permissions"
Write-Host ""

Write-Host "[3/5] Meetings tests..."

& $Python `
    -m pytest `
    .\tests\test_phase11_8_meetings_foundation.py `
    .\tests\test_phase11_8_meeting_lifecycle_contract.py `
    .\tests\test_phase11_8_meeting_migration_contract.py `
    .\tests\test_phase11_8_meeting_model_migration_parity.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Meetings regression failed."
}

Write-Host "PASS meetings"
Write-Host ""

Write-Host "[4/5] Monitoring + integration..."

& $Python `
    -m pytest `
    .\tests\test_phase11_8_meeting_self_and_monitoring.py `
    .\tests\test_phase11_8_monitoring_control_contract.py `
    .\tests\test_phase11_8_integration_contract.py `
    .\tests\test_phase11_8_router_order_contract.py `
    .\tests\test_phase11_8_security_regression.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Monitoring integration failed."
}

Write-Host "PASS monitoring"
Write-Host ""

Write-Host "[5/5] Final contract..."

& $Python `
    -m pytest `
    .\tests\test_phase11_8_final_contract.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Final contract failed."
}

Write-Host "PASS final contract"
Write-Host ""

Write-Host "================================================="
Write-Host " PHASE 11.8 FULL REGRESSION: PASS"
Write-Host "================================================="