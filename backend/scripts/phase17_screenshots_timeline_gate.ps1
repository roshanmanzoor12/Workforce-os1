$ErrorActionPreference = "Stop"

Set-Location "C:\workforce-os\backend"


Write-Host ""
Write-Host "================================================"
Write-Host " WorkforceOS Phase 17.1 Screenshots/Timeline Gate"
Write-Host "================================================"


# =========================================================
# 1. WIRE
# =========================================================

Write-Host ""
Write-Host "[1/10] Wire Phase 17 screenshot/timeline hardening..."

& ".\.venv\Scripts\python.exe" `
    ".\scripts\phase17_wire_screenshots_timeline.py"

if ($LASTEXITCODE -ne 0) {
    throw "Phase 17 wiring failed."
}


# =========================================================
# 2. COMPILE
# =========================================================

Write-Host ""
Write-Host "[2/10] Compile screenshot/timeline modules..."

& ".\.venv\Scripts\python.exe" `
    -m compileall `
    ".\app\modules\live_monitoring" `
    ".\app\modules\timeline" `
    ".\app\modules\audit_log" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 17 compile failed."
}

Write-Host "PASS compile"


# =========================================================
# 3. IMPORTS
# =========================================================

Write-Host ""
Write-Host "[3/10] Import Phase 17 stack..."

& ".\.venv\Scripts\python.exe" `
    -c "from app.modules.live_monitoring.models import SCREENSHOT_STATUS_FAILED; from app.modules.live_monitoring.service import LiveMonitoringService; from app.modules.timeline.sources import ScreenshotTimelineSource; from app.modules.timeline.enums import TimelineSourceKey; print('PASS Phase 17 imports', SCREENSHOT_STATUS_FAILED, TimelineSourceKey.SCREENSHOTS)"

if ($LASTEXITCODE -ne 0) {
    throw "Phase 17 imports failed."
}


# =========================================================
# 4. ROUTES
# =========================================================

Write-Host ""
Write-Host "[4/10] Screenshot/timeline route contract..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\monitoring\test_phase17_routes.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 17 route contract failed."
}


# =========================================================
# 5. LIFECYCLE
# =========================================================

Write-Host ""
Write-Host "[5/10] Screenshot lifecycle contract..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\monitoring\test_phase17_screenshot_lifecycle.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 17 lifecycle contract failed."
}


# =========================================================
# 6. FILTERS / RETENTION
# =========================================================

Write-Host ""
Write-Host "[6/10] Filters and retention contract..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\monitoring\test_phase17_filters_retention.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 17 filters/retention contract failed."
}


# =========================================================
# 7. PRIVACY / MEDIA / AUDIT
# =========================================================

Write-Host ""
Write-Host "[7/10] Privacy, media and audit contract..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\monitoring\test_phase17_privacy_media.py" `
    ".\tests\modules\monitoring\test_phase17_policy_audit_contract.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 17 privacy/audit contract failed."
}


# =========================================================
# 8. TIMELINE
# =========================================================

Write-Host ""
Write-Host "[8/10] Screenshot timeline contract..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\monitoring\test_phase17_timeline.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 17 timeline contract failed."
}


# =========================================================
# 9. MONITORING REGRESSION
# =========================================================

Write-Host ""
Write-Host "[9/10] Monitoring regression..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\monitoring" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Monitoring regression failed."
}


# =========================================================
# 10. DEVICE + PAYROLL REGRESSION
# =========================================================

Write-Host ""
Write-Host "[10/10] Device and payroll regression..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\devices" `
    ".\tests\modules\payroll" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Device/payroll regression failed."
}


Write-Host ""
Write-Host "================================================"
Write-Host " Phase 17.1 Screenshots/Timeline Gate PASS"
Write-Host "================================================"