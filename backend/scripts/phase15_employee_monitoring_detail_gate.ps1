$ErrorActionPreference = "Stop"

Set-Location "C:\workforce-os\backend"


Write-Host ""
Write-Host "================================================"
Write-Host " WorkforceOS Phase 15 Employee Monitoring Detail"
Write-Host "================================================"


# =========================================================
# 1. WIRE
# =========================================================

Write-Host ""
Write-Host "[1/9] Wire Employee Monitoring Detail router..."

& ".\.venv\Scripts\python.exe" `
    ".\scripts\phase15_wire_employee_monitoring_detail.py"

if ($LASTEXITCODE -ne 0) {
    throw "Phase 15 router wiring failed."
}


# =========================================================
# 2. COMPILE
# =========================================================

Write-Host ""
Write-Host "[2/9] Compile Phase 15 modules..."

& ".\.venv\Scripts\python.exe" `
    -m compileall `
    ".\app\modules\employee_monitoring_detail" `
    ".\app\modules\tenant_api\router.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 15 compile failed."
}

Write-Host "PASS compile"


# =========================================================
# 3. IMPORT
# =========================================================

Write-Host ""
Write-Host "[3/9] Import Employee Monitoring Detail stack..."

& ".\.venv\Scripts\python.exe" `
    -c "from app.modules.employee_monitoring_detail.router import router; from app.modules.employee_monitoring_detail.service import EmployeeMonitoringDetailService; from app.modules.employee_monitoring_detail.access import resolve_employee_monitoring_detail_access; print('PASS Phase 15 imports')"

if ($LASTEXITCODE -ne 0) {
    throw "Phase 15 import failed."
}


# =========================================================
# 4. ROUTE CONTRACT
# =========================================================

Write-Host ""
Write-Host "[4/9] Employee Monitoring Detail API contract..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\monitoring\test_phase15_employee_monitoring_detail_contract.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 15 API contract failed."
}


# =========================================================
# 5. TARGET SCOPE
# =========================================================

Write-Host ""
Write-Host "[5/9] Employee target-scope contract..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\monitoring\test_phase15_employee_monitoring_scope.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 15 target-scope contract failed."
}


# =========================================================
# 6. PRIVACY / EVIDENCE
# =========================================================

Write-Host ""
Write-Host "[6/9] Browser privacy + persisted evidence contract..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\monitoring\test_phase15_employee_monitoring_privacy.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 15 privacy/evidence contract failed."
}


# =========================================================
# 7. MONITORING REGRESSION
# =========================================================

Write-Host ""
Write-Host "[7/9] Monitoring regression..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\monitoring" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Monitoring regression failed."
}


# =========================================================
# 8. DEVICE REGRESSION
# =========================================================

Write-Host ""
Write-Host "[8/9] Device regression..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\devices" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Device regression failed."
}


# =========================================================
# 9. PAYROLL REGRESSION
# =========================================================

Write-Host ""
Write-Host "[9/9] Payroll regression..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\payroll" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Payroll regression failed."
}


Write-Host ""
Write-Host "================================================"
Write-Host " Phase 15 Employee Monitoring Detail Gate PASS"
Write-Host "================================================"