$ErrorActionPreference = "Stop"

Set-Location "C:\workforce-os\backend"


Write-Host ""
Write-Host "================================================"
Write-Host " WorkforceOS Phase 13.1 Device Baseline Gate"
Write-Host "================================================"


# =========================================================
# 1. COMPILE
# =========================================================

Write-Host ""
Write-Host "[1/8] Compile device + agent modules..."

& ".\.venv\Scripts\python.exe" `
    -m compileall `
    ".\app\modules\devices" `
    ".\app\modules\desktop_agent" `
    ".\tests\modules\devices" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Device/agent compile failed."
}

Write-Host "PASS compile"


# =========================================================
# 2. EXISTING FILE SURFACE
# =========================================================

Write-Host ""
Write-Host "[2/8] Device backend file surface..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\devices\test_phase13_1_device_files.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Device file surface failed."
}


# =========================================================
# 3. INVENTORY
# =========================================================

Write-Host ""
Write-Host "[3/8] Inventory contract..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\devices\test_phase13_1_inventory_contract.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Device inventory contract failed."
}


# =========================================================
# 4. ASSIGNMENT + CREDENTIALS
# =========================================================

Write-Host ""
Write-Host "[4/8] Assignment + credentials..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\devices\test_phase13_1_assignment_contract.py" `
    ".\tests\modules\devices\test_phase13_1_credentials_contract.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Device assignment/credential contract failed."
}


# =========================================================
# 5. REGISTRATION + AGENT
# =========================================================

Write-Host ""
Write-Host "[5/8] Registration + desktop agent..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\devices\test_phase13_1_registration_contract.py" `
    ".\tests\modules\devices\test_phase13_1_agent_contract.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Device registration/agent contract failed."
}


# =========================================================
# 6. SECURITY BOUNDARY
# =========================================================

Write-Host ""
Write-Host "[6/8] Device security boundary..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\devices\test_phase13_1_security_boundary.py" `
    ".\tests\modules\devices\test_phase13_1_architecture_dod.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Device security boundary failed."
}


# =========================================================
# 7. EXISTING DEVICE TESTS
# =========================================================

Write-Host ""
Write-Host "[7/8] Existing device tests..."

$ExistingTests = Get-ChildItem `
    ".\tests\modules\devices" `
    -File `
    -Filter "test_*.py" |
    Where-Object {
        $_.Name -notlike "test_phase13_1_*"
    }


if ($ExistingTests.Count -gt 0) {

    & ".\.venv\Scripts\python.exe" `
        -m pytest `
        ".\tests\modules\devices" `
        -q

    if ($LASTEXITCODE -ne 0) {
        throw "Existing device suite failed."
    }
}
else {
    Write-Host "No earlier device tests found."
}


# =========================================================
# 8. PREVIOUS PHASE REGRESSION
# =========================================================

Write-Host ""
Write-Host "[8/8] Phase 12 regression smoke..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\payroll" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Phase 12.3 Payroll regression failed."
}


Write-Host ""
Write-Host "================================================"
Write-Host " Phase 13.1 Device Baseline Gate PASS"
Write-Host "================================================"