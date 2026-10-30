$ErrorActionPreference = "Stop"

Set-Location "C:\workforce-os\backend"

Write-Host ""
Write-Host "================================================"
Write-Host " WorkforceOS Phase 12.2 Final Hardening Gate"
Write-Host "================================================"

Write-Host ""
Write-Host "[1/8] Wire integration router..."

& ".\.venv\Scripts\python.exe" `
    ".\scripts\phase12_2_wire_integration_router.py"

if ($LASTEXITCODE -ne 0) {
    throw "Integration router wiring failed."
}

Write-Host ""
Write-Host "[2/8] Compile integration modules..."

& ".\.venv\Scripts\python.exe" `
    -m py_compile `
    ".\app\modules\leave\calendar_schemas.py" `
    ".\app\modules\leave\calendar_query.py" `
    ".\app\modules\leave\integration_router.py" `
    ".\app\modules\attendance\leave_bridge.py" `
    ".\app\modules\tenant_api\router.py"

if ($LASTEXITCODE -ne 0) {
    throw "Integration compile failed."
}

Write-Host "PASS integration compile"

Write-Host ""
Write-Host "[3/8] Import integration surface..."

& ".\.venv\Scripts\python.exe" `
    -c "from app.modules.leave.calendar_query import LeaveCalendarQueryService; from app.modules.leave.integration_router import router; from app.modules.attendance.leave_bridge import AttendanceLeaveBridge; print('PASS final Leave integration imports')"

if ($LASTEXITCODE -ne 0) {
    throw "Integration import failed."
}

Write-Host ""
Write-Host "[4/8] New integration tests..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\leave\test_phase12_2_calendar_query_contract.py" `
    ".\tests\modules\leave\test_phase12_2_integration_router_contract.py" `
    ".\tests\modules\leave\test_phase12_2_payroll_period_math.py" `
    ".\tests\modules\attendance\test_phase12_2_leave_bridge.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "New integration tests failed."
}

Write-Host ""
Write-Host "[5/8] Full Phase 12.2 Leave suite..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\leave" `
    ".\tests\modules\attendance\test_phase12_2_leave_bridge.py" `
    ".\tests\modules\workspace_permissions\test_phase12_2_leave_permissions.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 12.2 Leave suite failed."
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
    throw "Tenant Alembic head failed."
}

Write-Host ""
Write-Host "[8/8] Runtime schema alignment..."

& ".\.venv\Scripts\python.exe" `
    -c "from app.db.tenant_initialization import CURRENT_TENANT_SCHEMA_VERSION; assert CURRENT_TENANT_SCHEMA_VERSION == 'n4i5j6k7l8m9'; print('PASS schema version:', CURRENT_TENANT_SCHEMA_VERSION)"

if ($LASTEXITCODE -ne 0) {
    throw "Runtime tenant schema version failed."
}

Write-Host ""
Write-Host "================================================"
Write-Host " Phase 12.2 Final Hardening Gate PASS"
Write-Host "================================================"
