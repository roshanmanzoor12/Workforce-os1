$ErrorActionPreference = "Stop"

Set-Location "C:\workforce-os\backend"

Write-Host ""
Write-Host "================================================"
Write-Host " WorkforceOS Phase 12.3 Audit Hardening Gate"
Write-Host "================================================"

Write-Host ""
Write-Host "[1/7] Compile Payroll hardening files..."

& ".\.venv\Scripts\python.exe" `
    -m py_compile `
    ".\app\modules\payroll\audit.py" `
    ".\app\modules\payroll\summary_schemas.py" `
    ".\app\modules\payroll\summary.py" `
    ".\app\modules\payroll\read_service.py" `
    ".\app\modules\payroll\router.py"

if ($LASTEXITCODE -ne 0) {
    throw "Payroll hardening compile failed."
}

Write-Host "PASS compile"

Write-Host ""
Write-Host "[2/7] Import hardening surface..."

& ".\.venv\Scripts\python.exe" `
    -c "from app.modules.payroll.audit import PayrollAuditService; from app.modules.payroll.summary import PayrollSummaryBuilder; from app.modules.payroll.read_service import PayrollReadService; from app.modules.payroll.router import router; print('PASS hardening imports')"

if ($LASTEXITCODE -ne 0) {
    throw "Payroll hardening imports failed."
}

Write-Host ""
Write-Host "[3/7] Audit + summary tests..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\payroll\test_phase12_3_summary.py" `
    ".\tests\modules\payroll\test_phase12_3_audit_contract.py" `
    ".\tests\modules\payroll\test_phase12_3_router_hardening.py" `
    ".\tests\modules\payroll\test_phase12_3_lock_immutability.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Payroll hardening tests failed."
}

Write-Host ""
Write-Host "[4/7] Full Payroll suite..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\payroll" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Full Payroll suite failed."
}

Write-Host ""
Write-Host "[5/7] Phase 12.2 regression..."

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
Write-Host "[6/7] Tenant migration graph..."

& ".\.venv\Scripts\python.exe" `
    -m alembic `
    -c ".\alembic.tenant.ini" `
    heads

if ($LASTEXITCODE -ne 0) {
    throw "Tenant migration graph failed."
}

Write-Host ""
Write-Host "[7/7] Runtime schema version..."

& ".\.venv\Scripts\python.exe" `
    -c "from app.db.tenant_initialization import CURRENT_TENANT_SCHEMA_VERSION; print('CURRENT_TENANT_SCHEMA_VERSION =', CURRENT_TENANT_SCHEMA_VERSION); assert CURRENT_TENANT_SCHEMA_VERSION == 'o5j6k7l8m9n0'; print('PASS runtime schema')"

if ($LASTEXITCODE -ne 0) {
    throw "Runtime schema version failed."
}

Write-Host ""
Write-Host "================================================"
Write-Host " Phase 12.3 Audit Hardening Gate PASS"
Write-Host "================================================"