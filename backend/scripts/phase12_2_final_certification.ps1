$ErrorActionPreference = "Stop"

Set-Location "C:\workforce-os\backend"

Write-Host ""
Write-Host "================================================"
Write-Host " WorkforceOS Phase 12.2 FINAL Certification"
Write-Host "================================================"

Write-Host ""
Write-Host "[1/9] Compile final Phase 12.2 files..."

& ".\.venv\Scripts\python.exe" `
    -m py_compile `
    ".\app\modules\leave\integration_router.py" `
    ".\scripts\phase12_2_disposable_tenant.py" `
    ".\scripts\phase12_2_migration_cert.py"

if ($LASTEXITCODE -ne 0) {
    throw "Phase 12.2 final compile failed."
}

Write-Host "PASS final compile"

Write-Host ""
Write-Host "[2/9] Runtime scope tests..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\leave\test_phase12_2_runtime_scope.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Runtime scope tests failed."
}

Write-Host ""
Write-Host "[3/9] Tenant isolation + audit tests..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\leave\test_phase12_2_tenant_isolation_contract.py" `
    ".\tests\modules\leave\test_phase12_2_audit_certification.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Tenant isolation/audit tests failed."
}

Write-Host ""
Write-Host "[4/9] API + migration + DoD tests..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\leave\test_phase12_2_api_surface_final.py" `
    ".\tests\modules\leave\test_phase12_2_migration_contract.py" `
    ".\tests\modules\leave\test_phase12_2_final_dod.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Final API/migration/DoD tests failed."
}

Write-Host ""
Write-Host "[5/9] Full Phase 12.2 suite..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\leave" `
    ".\tests\modules\attendance\test_phase12_2_leave_bridge.py" `
    ".\tests\modules\workspace_permissions\test_phase12_2_leave_permissions.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Full Phase 12.2 suite failed."
}

Write-Host ""
Write-Host "[6/9] Phase 12.1 regression..."

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
Write-Host "[7/9] Tenant migration graph..."

& ".\.venv\Scripts\python.exe" `
    -m alembic `
    -c ".\alembic.tenant.ini" `
    heads

if ($LASTEXITCODE -ne 0) {
    throw "Tenant migration graph failed."
}

Write-Host ""
Write-Host "[8/9] Runtime schema version..."

& ".\.venv\Scripts\python.exe" `
    -c "from app.db.tenant_initialization import CURRENT_TENANT_SCHEMA_VERSION; print('CURRENT_TENANT_SCHEMA_VERSION =', CURRENT_TENANT_SCHEMA_VERSION); assert CURRENT_TENANT_SCHEMA_VERSION == 'n4i5j6k7l8m9'"

if ($LASTEXITCODE -ne 0) {
    throw "Runtime schema version failed."
}

Write-Host ""
Write-Host "[9/9] Disposable PostgreSQL migration certification..."
Write-Host "This creates ONLY a random temporary tenant database."
Write-Host "It upgrades, downgrades, re-upgrades, then deletes it."

& ".\.venv\Scripts\python.exe" `
    ".\scripts\phase12_2_migration_cert.py"

if ($LASTEXITCODE -ne 0) {
    throw "Disposable migration certification failed."
}

Write-Host ""
Write-Host "================================================"
Write-Host " PHASE 12.2 FINAL CERTIFICATION PASS"
Write-Host "================================================"