$ErrorActionPreference = "Stop"

Set-Location "C:\workforce-os\backend"


Write-Host ""
Write-Host "================================================"
Write-Host " WorkforceOS Phase 16 Live Screens Gate"
Write-Host "================================================"


# =========================================================
# 1. WIRE READINESS
# =========================================================

Write-Host ""
Write-Host "[1/10] Wire Live Screen readiness..."

& ".\.venv\Scripts\python.exe" `
    ".\scripts\phase16_wire_live_screen_readiness.py"

if ($LASTEXITCODE -ne 0) {
    throw "Phase 16 readiness wiring failed."
}


# =========================================================
# 2. COMPILE
# =========================================================

Write-Host ""
Write-Host "[2/10] Compile Live Screen modules..."

& ".\.venv\Scripts\python.exe" `
    -m compileall `
    ".\app\modules\live_monitoring" `
    ".\app\modules\monitoring_admin" `
    ".\app\modules\devices" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 16 compile failed."
}

Write-Host "PASS compile"


# =========================================================
# 3. IMPORTS
# =========================================================

Write-Host ""
Write-Host "[3/10] Import Live Screen stack..."

& ".\.venv\Scripts\python.exe" `
    -c "from app.modules.live_monitoring.service import LiveMonitoringService; from app.modules.live_monitoring.live_screen_readiness import require_live_screen_ready; from app.modules.live_monitoring.router import router; print('PASS Phase 16 imports')"

if ($LASTEXITCODE -ne 0) {
    throw "Phase 16 imports failed."
}


# =========================================================
# 4. ROUTE CONTRACT
# =========================================================

Write-Host ""
Write-Host "[4/10] Live Screen route contract..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\monitoring\test_phase16_live_screen_routes.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 16 route contract failed."
}


# =========================================================
# 5. LIFECYCLE
# =========================================================

Write-Host ""
Write-Host "[5/10] Live Screen lifecycle contract..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\monitoring\test_phase16_live_screen_lifecycle.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 16 lifecycle contract failed."
}


# =========================================================
# 6. READINESS
# =========================================================

Write-Host ""
Write-Host "[6/10] Live Screen readiness/unavailable states..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\monitoring\test_phase16_live_screen_readiness.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 16 readiness contract failed."
}


# =========================================================
# 7. SCOPE / CONSENT / PRIVACY
# =========================================================

Write-Host ""
Write-Host "[7/10] Scope, consent and privacy..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\monitoring\test_phase16_live_screen_scope.py" `
    ".\tests\modules\monitoring\test_phase16_live_screen_consent_policy.py" `
    ".\tests\modules\monitoring\test_phase16_live_screen_privacy.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 16 security/privacy contract failed."
}


# =========================================================
# 8. MONITORING REGRESSION
# =========================================================

Write-Host ""
Write-Host "[8/10] Monitoring regression..."

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
Write-Host " Phase 16 Live Screens Gate PASS"
Write-Host "================================================"