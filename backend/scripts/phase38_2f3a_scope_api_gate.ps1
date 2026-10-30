$ErrorActionPreference = "Stop"

$backendRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $backendRoot

$env:PYTHONPATH = $backendRoot

$pythonExecutable = Join-Path `
    $backendRoot `
    ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $pythonExecutable)) {
    throw "Backend virtual environment Python was not found."
}

$phase38Files = @(
    ".\app\modules\workspace_rbac\scope_api_contract.py"
    ".\app\modules\workspace_rbac\scope_dependencies.py"
    ".\app\modules\workspace_rbac\scope_router.py"
    ".\app\modules\workspace_rbac\scope_registration.py"
    ".\tests\modules\workspace_permissions\test_phase38_scope_api_dependencies.py"
    ".\tests\modules\workspace_permissions\test_phase38_scope_api_routes.py"
    ".\tests\modules\workspace_permissions\test_phase38_scope_api_http.py"
    ".\tests\modules\workspace_permissions\test_phase38_scope_api_registration.py"
    ".\scripts\phase38_install_scope_api.py"
)

foreach ($file in $phase38Files) {
    if (-not (Test-Path -LiteralPath $file)) {
        throw "Required Phase 38.2F3A file is missing: $file"
    }
}

Write-Host "Checking Phase 38.2F3A syntax..."

& $pythonExecutable -m py_compile @phase38Files

if ($LASTEXITCODE -ne 0) {
    throw "Phase 38.2F3A syntax verification failed."
}

Write-Host "Checking API dependencies, routes, HTTP contracts, and registration..."

& $pythonExecutable -m pytest `
    ".\tests\modules\workspace_permissions\test_phase38_scope_api_dependencies.py" `
    ".\tests\modules\workspace_permissions\test_phase38_scope_api_routes.py" `
    ".\tests\modules\workspace_permissions\test_phase38_scope_api_http.py" `
    ".\tests\modules\workspace_permissions\test_phase38_scope_api_registration.py" `
    -q `
    --tb=short `
    --import-mode=importlib `
    --color=no

if ($LASTEXITCODE -ne 0) {
    throw "Phase 38.2F3A API verification failed."
}

Write-Host "Checking employee, project, permission, API key, and tenant regressions..."

& $pythonExecutable -m pytest `
    ".\tests\modules\employees" `
    ".\tests\modules\projects" `
    ".\tests\modules\workspace_permissions" `
    ".\tests\modules\api_keys" `
    ".\tests\test_phase11_7_tenant_context_contract.py" `
    ".\tests\test_phase11_8_workspace_permissions.py" `
    ".\tests\test_phase11_8_security_regression.py" `
    -q `
    --tb=short `
    --import-mode=importlib `
    --color=no

if ($LASTEXITCODE -ne 0) {
    throw "Phase 38.2F3A regression verification failed."
}

Write-Host "Inspecting control migration head..."

& $pythonExecutable -m alembic `
    -c ".\alembic-control.ini" `
    heads

if ($LASTEXITCODE -ne 0) {
    throw "Control migration head inspection failed."
}

& $pythonExecutable -m alembic `
    -c ".\alembic-control.ini" `
    current

if ($LASTEXITCODE -ne 0) {
    throw "Control database revision inspection failed."
}

Write-Host "PHASE38_2F3A_SCOPE_API_GATE_PASSED"