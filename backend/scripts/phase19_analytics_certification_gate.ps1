$ErrorActionPreference = "Stop"

Set-Location "C:\workforce-os\backend"

Write-Host ""
Write-Host "================================================"
Write-Host " WorkforceOS Phase 19 Analytics Gate"
Write-Host "================================================"


# =========================================================
# 1. COMPILE
# =========================================================

Write-Host ""
Write-Host "[1/9] Compile analytics stack..."

& ".\.venv\Scripts\python.exe" `
    -m compileall `
    ".\app\modules\analytics" `
    ".\tests\modules\analytics_phase19" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 19 compile failed."
}

Write-Host "PASS compile"


# =========================================================
# 2. IMPORTS
# =========================================================

Write-Host ""
Write-Host "[2/9] Import analytics contracts..."

& ".\.venv\Scripts\python.exe" `
    -c "from app.modules.analytics.router import router; from app.modules.analytics.service import AnalyticsService; from app.modules.analytics.repository import AnalyticsRepository; from app.modules.analytics.access import resolve_analytics_access; print('PASS Phase 19 imports')"

if ($LASTEXITCODE -ne 0) {
    throw "Phase 19 imports failed."
}


# =========================================================
# 3. ROUTES
# =========================================================

Write-Host ""
Write-Host "[3/9] Analytics route contract..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\analytics_phase19\test_phase19_routes.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 19 route contract failed."
}


# =========================================================
# 4. SCHEMA CONTRACT
# =========================================================

Write-Host ""
Write-Host "[4/9] Analytics schema contract..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\analytics_phase19\test_phase19_schema_surface.py" `
    ".\tests\modules\analytics_phase19\test_phase19_window.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 19 schema/window contract failed."
}


# =========================================================
# 5. ACCESS / SCOPE
# =========================================================

Write-Host ""
Write-Host "[5/9] Analytics permission scope..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\analytics_phase19\test_phase19_permissions.py" `
    ".\tests\modules\analytics_phase19\test_phase19_integrity.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 19 access contract failed."
}


# =========================================================
# 6. REPOSITORY
# =========================================================

Write-Host ""
Write-Host "[6/9] Analytics repository coverage..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\analytics_phase19\test_phase19_repository_surface.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 19 repository contract failed."
}


# =========================================================
# 7. SERVICE / TRENDS
# =========================================================

Write-Host ""
Write-Host "[7/9] Analytics service composition..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\analytics_phase19\test_phase19_service_composition.py" `
    ".\tests\modules\analytics_phase19\test_phase19_trends.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 19 service contract failed."
}


# =========================================================
# 8. EXISTING ANALYTICS / PRODUCTIVITY REGRESSION
# =========================================================

Write-Host ""
Write-Host "[8/9] Existing analytics regressions..."

$RegressionTargets = @(
    ".\tests\modules\analytics",
    ".\tests\modules\productivity",
    ".\tests\modules\productivity_insights"
)

$RanRegression = $false

foreach ($Target in $RegressionTargets) {
    if (Test-Path $Target) {
        $RanRegression = $true

        Write-Host ""
        Write-Host "Running regression:"
        Write-Host " $Target"

        & ".\.venv\Scripts\python.exe" `
            -m pytest `
            $Target `
            -q

        if ($LASTEXITCODE -ne 0) {
            throw "Phase 19 regression failed: $Target"
        }
    }
}

if (-not $RanRegression) {
    Write-Host "INFO no legacy analytics test directories found"
}


# =========================================================
# 9. MONITORING / ACTIVITY REGRESSION
# =========================================================

Write-Host ""
Write-Host "[9/9] Monitoring and activity regression..."

$FinalRegressionTargets = @(
    ".\tests\modules\monitoring",
    ".\tests\modules\activity",
    ".\tests\modules\app_tracking",
    ".\tests\modules\website_tracking",
    ".\tests\modules\work_sessions"
)

foreach ($Target in $FinalRegressionTargets) {
    if (Test-Path $Target) {
        Write-Host ""
        Write-Host "Running:"
        Write-Host " $Target"

        & ".\.venv\Scripts\python.exe" `
            -m pytest `
            $Target `
            -q

        if ($LASTEXITCODE -ne 0) {
            throw "Phase 19 final regression failed: $Target"
        }
    }
}


Write-Host ""
Write-Host "================================================"
Write-Host " Phase 19 Analytics Gate PASS"
Write-Host "================================================"