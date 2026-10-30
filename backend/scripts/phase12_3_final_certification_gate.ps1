$ErrorActionPreference = "Stop"

Set-Location "C:\workforce-os\backend"

Write-Host ""
Write-Host "================================================"
Write-Host " WorkforceOS Phase 12.3 FINAL Certification"
Write-Host "================================================"

Write-Host ""
Write-Host "[1/10] Compile Payroll..."

& ".\.venv\Scripts\python.exe" `
    -m compileall `
    ".\app\modules\payroll" `
    ".\tests\modules\payroll" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Payroll compile failed."
}

Write-Host "PASS compile"

Write-Host ""
Write-Host "[2/10] Required API contract..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\payroll\test_phase12_3_required_api.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Required Payroll API contract failed."
}

Write-Host ""
Write-Host "[3/10] Snapshot integrity..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\payroll\test_phase12_3_snapshot_integrity.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Payroll snapshot integrity failed."
}

Write-Host ""
Write-Host "[4/10] Payslip security..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\payroll\test_phase12_3_payslip_security.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Payslip security failed."
}

Write-Host ""
Write-Host "[5/10] Audit + lifecycle..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\payroll\test_phase12_3_audit_evidence.py" `
    ".\tests\modules\payroll\test_phase12_3_lifecycle_final.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Payroll audit/lifecycle failed."
}

Write-Host ""
Write-Host "[6/10] Migration contracts..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\payroll\test_phase12_3_migration_final.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Payroll migration contract failed."
}

Write-Host ""
Write-Host "[7/10] Final DoD..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\payroll\test_phase12_3_final_dod.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Payroll final DoD failed."
}

Write-Host ""
Write-Host "[8/10] Complete Payroll suite..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\payroll" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Complete Payroll suite failed."
}

Write-Host ""
Write-Host "[9/10] Phase 12.1 + 12.2 regression..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\shifts" `
    ".\tests\modules\holidays" `
    ".\tests\modules\leave" `
    ".\tests\modules\attendance\test_phase12_2_leave_bridge.py" `
    ".\tests\modules\workspace_permissions\test_phase12_1_permissions.py" `
    ".\tests\modules\workspace_permissions\test_phase12_2_leave_permissions.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 12.1/12.2 regression failed."
}

Write-Host ""
Write-Host "[10/10] Disposable migration certificate..."

& ".\scripts\phase12_3_disposable_migration_gate.ps1"

if ($LASTEXITCODE -ne 0) {
    throw "Disposable migration certification failed."
}

Write-Host ""
Write-Host "Runtime schema:"
& ".\.venv\Scripts\python.exe" `
    -c "from app.db.tenant_initialization import CURRENT_TENANT_SCHEMA_VERSION; print(CURRENT_TENANT_SCHEMA_VERSION); assert CURRENT_TENANT_SCHEMA_VERSION == 'p6k7l8m9n0o1'"

if ($LASTEXITCODE -ne 0) {
    throw "Runtime schema version failed."
}

Write-Host ""
Write-Host "================================================"
Write-Host " WorkforceOS Phase 12.3 FINAL CERTIFICATION PASS"
Write-Host "================================================"