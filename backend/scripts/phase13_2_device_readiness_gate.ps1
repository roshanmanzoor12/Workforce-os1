$ErrorActionPreference = "Stop"

Set-Location "C:\workforce-os\backend"


Write-Host ""
Write-Host "================================================"
Write-Host " WorkforceOS Phase 13.2 Device Readiness Gate"
Write-Host "================================================"


# =========================================================
# 1. WIRING
# =========================================================

Write-Host ""
Write-Host "[1/7] Wire readiness router..."

& ".\.venv\Scripts\python.exe" `
    ".\scripts\phase13_2_wire_device_readiness.py"

if ($LASTEXITCODE -ne 0) {
    throw "Device readiness wiring failed."
}


# =========================================================
# 2. COMPILE
# =========================================================

Write-Host ""
Write-Host "[2/7] Compile readiness module..."

& ".\.venv\Scripts\python.exe" `
    -m compileall `
    ".\app\modules\devices\readiness_types.py" `
    ".\app\modules\devices\readiness_schemas.py" `
    ".\app\modules\devices\readiness_policy.py" `
    ".\app\modules\devices\readiness_repository.py" `
    ".\app\modules\devices\readiness_access.py" `
    ".\app\modules\devices\readiness_service.py" `
    ".\app\modules\devices\readiness_router.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Device readiness compile failed."
}

Write-Host "PASS compile"


# =========================================================
# 3. IMPORT
# =========================================================

Write-Host ""
Write-Host "[3/7] Import readiness stack..."

& ".\.venv\Scripts\python.exe" `
    -c "from app.modules.devices.readiness_policy import evaluate_device_readiness; from app.modules.devices.readiness_service import DeviceReadinessService; from app.modules.devices.readiness_router import router; print('PASS readiness imports')"

if ($LASTEXITCODE -ne 0) {
    throw "Device readiness import failed."
}


# =========================================================
# 4. READINESS TESTS
# =========================================================

Write-Host ""
Write-Host "[4/7] Readiness policy + schema tests..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\devices\test_phase13_2_device_readiness.py" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Device readiness tests failed."
}


# =========================================================
# 5. ROUTE CONTRACT
# =========================================================

Write-Host ""
Write-Host "[5/7] Readiness API route contract..."

# FastAPI 0.137+ keeps included routers as _IncludedRouter nodes
# instead of flattening every child APIRoute into router.routes.
#
# Therefore the canonical verification surface is OpenAPI,
# which resolves the complete router tree exactly as clients/docs
# see it.

& ".\.venv\Scripts\python.exe" `
    -c "from fastapi import FastAPI; from app.modules.tenant_api.router import router; app=FastAPI(); app.include_router(router); schema=app.openapi(); path='/workspaces/{workspace_id}/devices/readiness'; assert path in schema['paths'], f'Missing readiness OpenAPI path: {path}'; assert 'get' in schema['paths'][path], f'Missing GET operation for readiness path: {path}'; print('PASS readiness API route:', path)"

if ($LASTEXITCODE -ne 0) {
    throw "Device readiness route contract failed."
}


# =========================================================
# 6. DEVICE REGRESSION
# =========================================================

Write-Host ""
Write-Host "[6/7] Complete device regression suite..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\devices" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Device regression suite failed."
}


# =========================================================
# 7. PAYROLL REGRESSION
# =========================================================

Write-Host ""
Write-Host "[7/7] Phase 12.3 Payroll regression..."

& ".\.venv\Scripts\python.exe" `
    -m pytest `
    ".\tests\modules\payroll" `
    -q

if ($LASTEXITCODE -ne 0) {
    throw "Payroll regression failed."
}


Write-Host ""
Write-Host "================================================"
Write-Host " Phase 13.2 Device Readiness Gate PASS"
Write-Host "================================================"