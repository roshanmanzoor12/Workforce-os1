$ErrorActionPreference = "Stop"

Set-Location "C:\workforce-os\backend"

Write-Host ""
Write-Host "================================================"
Write-Host " WorkforceOS Phase 12.3 Calculation Gate"
Write-Host "================================================"

Write-Host ""
Write-Host "[1/8] Compile authoritative Payroll sources..."

& ".\.venv\Scripts\python.exe" `
    -m py_compile `
    ".\app\modules\payroll\source_schemas.py" `
    ".\app\modules\payroll\schedule_source.py" `
    ".\app\modules\payroll\attendance_source.py" `
    ".\app\modules\payroll\leave_source.py" `
    ".\app\modules\payroll\source_assembler.py" `
    ".\app\modules\payroll\calculation_service.py" `
    ".\app\modules\payroll\audit.py" `
    ".\app\modules\payroll\router.py"

if ($LASTEXITCODE -ne 0) {
    throw "Authoritative Payroll compile failed."
}

Write-Host "PASS compile"

Write-Host ""
Write-Host "[2/8] Import source adapters..."

& ".\.venv\Scripts\python.exe" `
    -c "from app.modules.payroll.schedule_source import PayrollScheduleSourceService; from app.modules.payroll.attendance_source import PayrollAttendanceSourceService; from app.modules.payroll.leave_source import PayrollLeaveSourceService; from app.modules.payroll.source_assembler import PayrollSourceAssembler; from app.modules.payroll.calculation_service import PayrollCalculationService; print('PASS Payroll authoritative source imports')"

if ($LASTEXITCODE -ne 0) {
    throw "Payroll source import failed."
}

Write-Host ""
Write-Host "[3/8] Authoritative calculation contracts..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\payroll\test_phase12_3_authoritative_calculation.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Authoritative calculation tests failed."
}

Write-Host ""
Write-Host "[4/8] Full Payroll suite..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\payroll" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Full Payroll suite failed."
}

Write-Host ""
Write-Host "[5/8] Phase 12.2 regression..."

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
Write-Host "[6/8] Phase 12.1 regression..."

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
Write-Host "[7/8] Tenant migration head..."

& ".\.venv\Scripts\python.exe" `
    -m alembic `
    -c ".\alembic.tenant.ini" `
    heads

if ($LASTEXITCODE -ne 0) {
    throw "Tenant migration graph failed."
}

Write-Host ""
Write-Host "[8/8] Runtime schema alignment..."

& ".\.venv\Scripts\python.exe" `
    -c "from app.db.tenant_initialization import CURRENT_TENANT_SCHEMA_VERSION; assert CURRENT_TENANT_SCHEMA_VERSION == 'o5j6k7l8m9n0'; print('PASS runtime schema:', CURRENT_TENANT_SCHEMA_VERSION)"

if ($LASTEXITCODE -ne 0) {
    throw "Runtime schema mismatch."
}

Write-Host ""
Write-Host "================================================"
Write-Host " Phase 12.3 Authoritative Calculation Gate PASS"
Write-Host "================================================"