$ErrorActionPreference = "Stop"

Set-Location "C:\workforce-os\backend"


Write-Host ""
Write-Host "================================================"
Write-Host " WorkforceOS Phase 17.2 Final Screenshot Gate"
Write-Host "================================================"


# =========================================================
# 1. COMPILE
# =========================================================

Write-Host ""
Write-Host "[1/10] Compile Phase 17.2 stack..."

& ".\.venv\Scripts\python.exe" `
    -m compileall `
    ".\app\modules\monitoring_admin" `
    ".\app\modules\live_monitoring" `
    ".\migrations\tenant\versions\q7l8m9n0o1p2_phase17_2_screenshot_cadence.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 17.2 compile failed."
}

Write-Host "PASS compile"


# =========================================================
# 2. IMPORTS
# =========================================================

Write-Host ""
Write-Host "[2/10] Import policy and retention stack..."

& ".\.venv\Scripts\python.exe" `
    -c "from app.modules.monitoring_admin.models import MonitoringAdminPolicy; from app.modules.monitoring_admin.service import MonitoringAdminService; from app.modules.live_monitoring.screenshot_retention import ScreenshotRetentionService; print('PASS Phase 17.2 imports')"

if ($LASTEXITCODE -ne 0) {
    throw "Phase 17.2 imports failed."
}


# =========================================================
# 3. TENANT MIGRATION HEAD
# =========================================================

Write-Host ""
Write-Host "[3/10] Verify tenant migration head..."

$Heads = & ".\.venv\Scripts\python.exe" `
    -m alembic `
    -c ".\alembic.tenant.ini" `
    heads

$Heads | Write-Host

if (
    $LASTEXITCODE -ne 0 -or
    ($Heads -join "`n") -notmatch "q7l8m9n0o1p2"
) {
    throw "Phase 17.2 tenant migration head failed."
}

Write-Host "PASS tenant migration head"


# =========================================================
# 4. CADENCE POLICY
# =========================================================

Write-Host ""
Write-Host "[4/10] Screenshot cadence policy contract..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\monitoring\test_phase17_2_policy_cadence.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 17.2 cadence policy tests failed."
}


# =========================================================
# 5. RETENTION CLEANUP
# =========================================================

Write-Host ""
Write-Host "[5/10] Physical retention cleanup contract..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\monitoring\test_phase17_2_retention_cleanup.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 17.2 retention cleanup tests failed."
}


# =========================================================
# 6. API / WORKSPACE SCOPE / STORAGE
# =========================================================

Write-Host ""
Write-Host "[6/10] API, cross-workspace and storage contract..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\monitoring\test_phase17_2_api_scope_storage.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 17.2 API/scope/storage tests failed."
}


# =========================================================
# 7. PHASE 17.1 REGRESSION
# =========================================================

Write-Host ""
Write-Host "[7/10] Phase 17.1 regression..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\monitoring\test_phase17_routes.py" `
    ".\tests\modules\monitoring\test_phase17_screenshot_lifecycle.py" `
    ".\tests\modules\monitoring\test_phase17_filters_retention.py" `
    ".\tests\modules\monitoring\test_phase17_privacy_media.py" `
    ".\tests\modules\monitoring\test_phase17_timeline.py" `
    ".\tests\modules\monitoring\test_phase17_policy_audit_contract.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 17.1 regression failed."
}


# =========================================================
# 8. MONITORING REGRESSION
# =========================================================

Write-Host ""
Write-Host "[8/10] Full monitoring regression..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\monitoring" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Monitoring regression failed."
}


# =========================================================
# 9. DEVICE REGRESSION
# =========================================================

Write-Host ""
Write-Host "[9/10] Device regression..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\devices" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Device regression failed."
}


# =========================================================
# 10. PAYROLL REGRESSION
# =========================================================

Write-Host ""
Write-Host "[10/10] Payroll regression..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\payroll" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Payroll regression failed."
}


Write-Host ""
Write-Host "================================================"
Write-Host " Phase 17.2 Final Screenshot Gate PASS"
Write-Host "================================================"