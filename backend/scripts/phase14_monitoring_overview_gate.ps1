$ErrorActionPreference = "Stop"

Set-Location "C:\workforce-os\backend"


Write-Host ""
Write-Host "================================================"
Write-Host " WorkforceOS Phase 14 Monitoring Overview Gate"
Write-Host "================================================"


# =========================================================
# 1. COMPILE
# =========================================================

Write-Host ""
Write-Host "[1/9] Compile monitoring evidence modules..."

$Paths = @(
    ".\app\modules\monitoring_control",
    ".\app\modules\monitoring_admin",
    ".\app\modules\activity",
    ".\app\modules\app_tracking",
    ".\app\modules\website_tracking",
    ".\app\modules\work_sessions",
    ".\app\modules\devices",
    ".\app\modules\timeline",
    ".\app\modules\workforce_intelligence"
)

foreach ($Path in $Paths) {
    if (Test-Path $Path) {
        & ".\.venv\Scripts\python.exe" `
            -m compileall `
            $Path `
            -q

        if ($LASTEXITCODE -ne 0) {
            throw "Compile failed: $Path"
        }
    }
}

Write-Host "PASS compile"


# =========================================================
# 2. MONITORING ROUTES
# =========================================================

Write-Host ""
Write-Host "[2/9] Monitoring Overview production routes..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\monitoring\test_phase14_monitoring_overview_routes.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Monitoring Overview route contract failed."
}


# =========================================================
# 3. SCOPE / RBAC
# =========================================================

Write-Host ""
Write-Host "[3/9] Monitoring scope/RBAC contract..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\monitoring\test_phase14_scope_contract.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Monitoring scope contract failed."
}


# =========================================================
# 4. WORKSPACE POLICY
# =========================================================

Write-Host ""
Write-Host "[4/9] Monitoring policy contract..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\monitoring\test_phase14_policy_contract.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Monitoring policy contract failed."
}


# =========================================================
# 5. READINESS
# =========================================================

Write-Host ""
Write-Host "[5/9] Device readiness overview contract..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\monitoring\test_phase14_readiness_contract.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Monitoring readiness contract failed."
}


# =========================================================
# 6. PERSISTED EVIDENCE
# =========================================================

Write-Host ""
Write-Host "[6/9] Persisted monitoring evidence contract..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\monitoring\test_phase14_evidence_sources.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Monitoring evidence contract failed."
}


# =========================================================
# 7. PRIVACY / SECRET BOUNDARY
# =========================================================

Write-Host ""
Write-Host "[7/9] Monitoring privacy/browser boundary..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\monitoring\test_phase14_privacy_contract.py" `
    ".\tests\modules\monitoring\test_phase14_browser_secret_boundary.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Monitoring privacy boundary failed."
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
Write-Host " Phase 14 Monitoring Overview Gate PASS"
Write-Host "================================================"