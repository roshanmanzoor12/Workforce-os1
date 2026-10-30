$ErrorActionPreference = "Stop"

Set-Location "C:\workforce-os\backend"


Write-Host ""
Write-Host "================================================"
Write-Host " WorkforceOS Phase 13.3 Agent Signals Gate"
Write-Host "================================================"


# =========================================================
# 1. COMPILE
# =========================================================

Write-Host ""
Write-Host "[1/9] Compile activity/app signal modules..."

$Paths = @(
    ".\app\modules\activity",
    ".\app\modules\app_tracking",
    ".\app\modules\desktop_agent",
    ".\app\modules\devices"
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
# 2. PRODUCTION OPENAPI
# =========================================================

Write-Host ""
Write-Host "[2/9] Production device-agent OpenAPI contract..."

& ".\.venv\Scripts\python.exe" `
    -c "from app.main import app; from app.config import settings; p=settings.api_v1_prefix.rstrip('/'); s=app.openapi()['paths']; expected={(p+'/device-agent/activity-state','post'),(p+'/device-agent/activity-status','get'),(p+'/device-agent/app-observation','post'),(p+'/device-agent/app-status','get'),(p+'/device-agent/app-history','get')}; missing=[(x,m) for x,m in sorted(expected) if x not in s or m not in s[x]]; assert not missing, f'Missing agent signal routes: {missing}'; print('PASS production agent signal OpenAPI')"

if ($LASTEXITCODE -ne 0) {
    throw "Production agent signal OpenAPI failed."
}


# =========================================================
# 3. ACTIVITY CONTRACT
# =========================================================

Write-Host ""
Write-Host "[3/9] Activity endpoint contract..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\devices\test_phase13_3_activity_contract.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Activity endpoint contract failed."
}


# =========================================================
# 4. APPLICATION CONTRACT
# =========================================================

Write-Host ""
Write-Host "[4/9] Foreground application contract..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\devices\test_phase13_3_app_observation_contract.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Application observation contract failed."
}


# =========================================================
# 5. AUTH / PRIVACY
# =========================================================

Write-Host ""
Write-Host "[5/9] Agent authentication/privacy boundary..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\devices\test_phase13_3_agent_auth_boundary.py" `
    ".\tests\modules\devices\test_phase13_3_privacy_contract.py" `
    ".\tests\modules\devices\test_phase13_3_device_secret_boundary.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Agent authentication/privacy boundary failed."
}


# =========================================================
# 6. METHOD CONTRACT
# =========================================================

Write-Host ""
Write-Host "[6/9] Agent signal HTTP method contract..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\devices\test_phase13_3_signal_methods.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Agent signal method contract failed."
}


# =========================================================
# 7. READINESS BRIDGE
# =========================================================

Write-Host ""
Write-Host "[7/9] Readiness bridge..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\devices\test_phase13_3_readiness_bridge.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Agent signal/readiness bridge failed."
}


# =========================================================
# 8. DEVICES REGRESSION
# =========================================================

Write-Host ""
Write-Host "[8/9] Complete devices regression..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\devices" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Devices regression failed."
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
Write-Host " Phase 13.3 Agent Signals Gate PASS"
Write-Host "================================================"