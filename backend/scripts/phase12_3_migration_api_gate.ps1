$ErrorActionPreference = "Stop"

Set-Location "C:\workforce-os\backend"

Write-Host ""
Write-Host "================================================"
Write-Host " WorkforceOS Phase 12.3 Migration + API Gate"
Write-Host "================================================"

Write-Host ""
Write-Host "[1/9] Wire Payroll..."

& ".\.venv\Scripts\python.exe" `
    ".\scripts\phase12_3_wire_payroll.py"

if ($LASTEXITCODE -ne 0) {
    throw "Payroll wiring failed."
}

Write-Host ""
Write-Host "[2/9] Compile Payroll API + migration..."

& ".\.venv\Scripts\python.exe" `
    -m py_compile `
    ".\app\modules\payroll\access_service.py" `
    ".\app\modules\payroll\lifecycle.py" `
    ".\app\modules\payroll\service.py" `
    ".\app\modules\payroll\router.py" `
    ".\migrations\tenant\versions\o5j6k7l8m9n0_phase12_3_payroll_foundation.py" `
    ".\scripts\phase12_3_wire_payroll.py"

if ($LASTEXITCODE -ne 0) {
    throw "Payroll API/migration compile failed."
}

Write-Host "PASS compile"

Write-Host ""
Write-Host "[3/9] Import Payroll API surface..."

& ".\.venv\Scripts\python.exe" `
    -c "from app.modules.payroll.router import router; from app.modules.payroll.access_service import PayrollAccessService; from app.modules.payroll.lifecycle import PayrollRunLifecycle; from app.modules.payroll.service import PayrollService; print('PASS Payroll API imports')"

if ($LASTEXITCODE -ne 0) {
    throw "Payroll API import failed."
}

Write-Host ""
Write-Host "[4/9] Payroll access/API/lifecycle tests..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\payroll\test_phase12_3_access_contract.py" `
    ".\tests\modules\payroll\test_phase12_3_api_lifecycle_contract.py" `
    ".\tests\modules\payroll\test_phase12_3_migration_contract.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Payroll access/API/lifecycle tests failed."
}

Write-Host ""
Write-Host "[5/9] Full Payroll suite..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\payroll" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Full Payroll suite failed."
}

Write-Host ""
Write-Host "[6/9] Phase 12.2 regression..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\leave" `
    ".\tests\modules\attendance\test_phase12_2_leave_bridge.py" `
    ".\tests\modules\workspace_permissions\test_phase12_2_leave_permissions.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 12.2 regression failed."
}

Write-Host ""
Write-Host "[7/9] Phase 12.1 regression..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\shifts" `
    ".\tests\modules\holidays" `
    ".\tests\modules\workspace_permissions\test_phase12_1_permissions.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 12.1 regression failed."
}

Write-Host ""
Write-Host "[8/9] Tenant migration head..."

& ".\.venv\Scripts\python.exe" `
    -m alembic `
    -c ".\alembic.tenant.ini" `
    heads

if ($LASTEXITCODE -ne 0) {
    throw "Tenant migration graph failed."
}

Write-Host ""
Write-Host "[9/9] Runtime schema alignment..."

& ".\.venv\Scripts\python.exe" `
    -c "from app.db.tenant_initialization import CURRENT_TENANT_SCHEMA_VERSION; print('CURRENT_TENANT_SCHEMA_VERSION =', CURRENT_TENANT_SCHEMA_VERSION); assert CURRENT_TENANT_SCHEMA_VERSION == 'o5j6k7l8m9n0'; print('PASS schema version')"

if ($LASTEXITCODE -ne 0) {
    throw "Runtime schema alignment failed."
}

Write-Host ""
Write-Host "================================================"
Write-Host " Phase 12.3 Migration + API Gate PASS"
Write-Host "================================================"