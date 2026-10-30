$ErrorActionPreference = "Stop"

Set-Location "C:\workforce-os\backend"

Write-Host ""
Write-Host "================================================"
Write-Host " WorkforceOS Phase 18 Productivity Gate"
Write-Host "================================================"

Write-Host ""
Write-Host "[1/9] Compile productivity stack..."

& ".\.venv\Scripts\python.exe" `
    -m compileall `
    ".\app\modules\productivity_insights" `
    ".\app\modules\analytics" `
    ".\app\modules\work_sessions" `
    ".\app\modules\activity" `
    ".\app\modules\app_tracking" `
    ".\app\modules\website_tracking" `
    ".\app\modules\ai_productivity" `
    ".\tests\modules\productivity" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 18 compile failed."
}

Write-Host "PASS compile"

Write-Host ""
Write-Host "[2/9] Import Phase 18 contracts..."

& ".\.venv\Scripts\python.exe" `
    -c "from app.modules.productivity_insights.service import ProductivityInsightsService; from app.modules.analytics.service import AnalyticsService; from app.modules.work_sessions.service import WorkSessionService; from app.modules.ai_productivity.service import AIProductivityService; print('PASS Phase 18 imports')"

if ($LASTEXITCODE -ne 0) {
    throw "Phase 18 imports failed."
}

Write-Host ""
Write-Host "[3/9] Productivity route contract..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\productivity\test_phase18_routes.py" `
    ".\tests\modules\productivity\test_phase18_timeline_surface.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 18 route contract failed."
}

Write-Host ""
Write-Host "[4/9] Schema and analytics contract..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\productivity\test_phase18_schema_surface.py" `
    ".\tests\modules\productivity\test_phase18_analytics_bridge.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 18 analytics contract failed."
}

Write-Host ""
Write-Host "[5/9] Work-session accounting..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\productivity\test_phase18_work_sessions.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 18 work-session contract failed."
}

Write-Host ""
Write-Host "[6/9] Productivity permission scope..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\productivity\test_phase18_permissions.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 18 permission contract failed."
}

Write-Host ""
Write-Host "[7/9] No-score and AI boundary..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\productivity\test_phase18_no_opaque_scoring.py" `
    ".\tests\modules\productivity\test_phase18_ai_boundary.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 18 safety/AI contract failed."
}

Write-Host ""
Write-Host "[8/9] Existing productivity regressions..."

$RegressionTargets = @(
    ".\tests\modules\productivity_insights",
    ".\tests\modules\analytics",
    ".\tests\modules\work_sessions",
    ".\tests\modules\activity",
    ".\tests\modules\app_tracking",
    ".\tests\modules\website_tracking"
)

$RanAnyRegression = $false

foreach ($Target in $RegressionTargets) {
    if (Test-Path $Target) {
        $RanAnyRegression = $true

        Write-Host ""
        Write-Host "Running regression:"
        Write-Host " $Target"

        & ".\.venv\Scripts\python.exe" `
            -m pytest `
            $Target `
            -q

        if ($LASTEXITCODE -ne 0) {
            throw "Phase 18 regression failed: $Target"
        }
    }
}

if (-not $RanAnyRegression) {
    Write-Host "INFO no legacy productivity test directories found"
}

Write-Host ""
Write-Host "[9/9] Monitoring regression..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\monitoring" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 18 monitoring regression failed."
}

Write-Host "PASS monitoring regression"

Write-Host ""
Write-Host "================================================"
Write-Host " Phase 18 Productivity Gate PASS"
Write-Host "================================================"
