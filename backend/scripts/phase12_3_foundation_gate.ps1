$ErrorActionPreference = "Stop"

Set-Location "C:\workforce-os\backend"

Write-Host ""
Write-Host "================================================"
Write-Host " WorkforceOS Phase 12.3 Payroll Foundation Gate"
Write-Host "================================================"

Write-Host ""
Write-Host "[1/7] Verify payroll files..."

$Files = @(
    ".\app\modules\payroll\models.py",
    ".\app\modules\payroll\schemas.py",
    ".\app\modules\payroll\repository.py",
    ".\app\modules\payroll\calculator.py",
    ".\app\modules\payroll\service.py",
    ".\app\modules\payroll\events.py",
    ".\app\modules\payroll\permissions.py",
    ".\tests\modules\payroll\test_phase12_3_calculator.py",
    ".\tests\modules\payroll\test_phase12_3_domain_contract.py"
)

foreach ($File in $Files) {
    if (-not (Test-Path $File)) {
        throw "Missing required file: $File"
    }
}

Write-Host "PASS files present"

Write-Host ""
Write-Host "[2/7] Compile payroll module..."

& ".\.venv\Scripts\python.exe" `
    -m py_compile `
    ".\app\modules\payroll\models.py" `
    ".\app\modules\payroll\schemas.py" `
    ".\app\modules\payroll\repository.py" `
    ".\app\modules\payroll\calculator.py" `
    ".\app\modules\payroll\service.py" `
    ".\app\modules\payroll\events.py" `
    ".\app\modules\payroll\permissions.py"

if ($LASTEXITCODE -ne 0) {
    throw "Payroll compile failed."
}

Write-Host "PASS payroll compile"

Write-Host ""
Write-Host "[3/7] Import payroll foundation..."

& ".\.venv\Scripts\python.exe" `
    -c "from app.modules.payroll.models import CompensationContract, PayrollRun, PayrollCalculation, PayrollAdjustment; from app.modules.payroll.calculator import PayrollCalculator; from app.modules.payroll.service import PayrollService; print('PASS payroll foundation imports')"

if ($LASTEXITCODE -ne 0) {
    throw "Payroll import failed."
}

Write-Host ""
Write-Host "[4/7] Payroll calculator tests..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\payroll\test_phase12_3_calculator.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Payroll calculator tests failed."
}

Write-Host ""
Write-Host "[5/7] Payroll domain contract tests..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\payroll\test_phase12_3_domain_contract.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Payroll domain contract tests failed."
}

Write-Host ""
Write-Host "[6/7] Phase 12.2 regression..."

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
Write-Host "[7/7] Existing tenant migration head..."

& ".\.venv\Scripts\python.exe" `
    -m alembic `
    -c ".\alembic.tenant.ini" `
    heads

if ($LASTEXITCODE -ne 0) {
    throw "Tenant migration graph failed."
}

Write-Host ""
Write-Host "================================================"
Write-Host " Phase 12.3 Payroll Foundation Gate PASS"
Write-Host "================================================"