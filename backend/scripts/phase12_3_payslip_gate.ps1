$ErrorActionPreference = "Stop"

Set-Location "C:\workforce-os\backend"

Write-Host ""
Write-Host "================================================"
Write-Host " WorkforceOS Phase 12.3 Payslip Gate"
Write-Host "================================================"

Write-Host ""
Write-Host "[1/9] Wire Payslips..."

& ".\.venv\Scripts\python.exe" `
    ".\scripts\phase12_3_wire_payslips.py"

if ($LASTEXITCODE -ne 0) {
    throw "Payslip wiring failed."
}

Write-Host ""
Write-Host "[2/9] Compile Payslip files..."

& ".\.venv\Scripts\python.exe" `
    -m py_compile `
    ".\app\modules\payroll\payslip_models.py" `
    ".\app\modules\payroll\payslip_schemas.py" `
    ".\app\modules\payroll\payslip_repository.py" `
    ".\app\modules\payroll\payslip_service.py" `
    ".\app\modules\payroll\payslip_access.py" `
    ".\app\modules\payroll\payslip_router.py" `
    ".\migrations\tenant\versions\p6k7l8m9n0o1_phase12_3_payroll_payslips.py"

if ($LASTEXITCODE -ne 0) {
    throw "Payslip compile failed."
}

Write-Host "PASS compile"

Write-Host ""
Write-Host "[3/9] Import Payslip surface..."

& ".\.venv\Scripts\python.exe" `
    -c "from app.modules.payroll.payslip_models import PayrollPayslip; from app.modules.payroll.payslip_service import PayrollPayslipService; from app.modules.payroll.payslip_router import router; print('PASS Payslip imports')"

if ($LASTEXITCODE -ne 0) {
    throw "Payslip import failed."
}

Write-Host ""
Write-Host "[4/9] Payslip tests..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\payroll\test_phase12_3_payslips.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Payslip tests failed."
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
Write-Host "[9/9] Runtime schema version..."

& ".\.venv\Scripts\python.exe" `
    -c "from app.db.tenant_initialization import CURRENT_TENANT_SCHEMA_VERSION; print('CURRENT_TENANT_SCHEMA_VERSION =', CURRENT_TENANT_SCHEMA_VERSION); assert CURRENT_TENANT_SCHEMA_VERSION == 'p6k7l8m9n0o1'; print('PASS runtime schema')"

if ($LASTEXITCODE -ne 0) {
    throw "Payslip runtime schema failed."
}

Write-Host ""
Write-Host "================================================"
Write-Host " Phase 12.3 Payslip Gate PASS"
Write-Host "================================================"