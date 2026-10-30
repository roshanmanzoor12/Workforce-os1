$ErrorActionPreference = "Stop"

$backendDirectory = Split-Path -Parent $PSScriptRoot
Set-Location $backendDirectory
$env:PYTHONPATH = $backendDirectory

$python = Join-Path $backendDirectory ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $python)) {
    throw "Backend virtual environment Python was not found."
}

$sourceFiles = @(
    ".\app\db\tenant_dependency.py"
    ".\app\modules\workspace_permissions\request_scopes.py"
    ".\app\modules\employees\scope_access.py"
    ".\app\modules\employees\access_service.py"
    ".\app\modules\projects\router.py"
    ".\tests\modules\workspace_permissions\test_phase38_request_saved_scopes.py"
    ".\tests\modules\workspace_permissions\test_phase38_scope_control_session.py"
    ".\tests\modules\employees\test_phase38_saved_scope_loading.py"
    ".\tests\modules\projects\test_phase38_project_saved_scope_loading.py"
)

foreach ($file in $sourceFiles) {
    if (-not (Test-Path -LiteralPath $file)) {
        throw "Required file missing: $file"
    }
}

Write-Host "Checking Phase 38.2F3B syntax..."

& $python -m py_compile @sourceFiles

if ($LASTEXITCODE -ne 0) {
    throw "Phase 38.2F3B syntax verification failed."
}

Write-Host "Checking automatic saved-scope loading..."

& $python -m pytest `
    ".\tests\modules\workspace_permissions\test_phase38_request_saved_scopes.py" `
    ".\tests\modules\workspace_permissions\test_phase38_scope_control_session.py" `
    ".\tests\modules\employees\test_phase38_saved_scope_loading.py" `
    ".\tests\modules\projects\test_phase38_project_saved_scope_loading.py" `
    -q `
    --tb=short `
    --import-mode=importlib `
    --color=no

if ($LASTEXITCODE -ne 0) {
    throw "Automatic saved-scope loading verification failed."
}

Write-Host "Checking employee, project, permission, API key, and tenant regressions..."

& $python -m pytest `
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
    throw "Phase 38.2F3B regression verification failed."
}

Write-Host "Inspecting control migration head..."

& $python -m alembic -c ".\alembic-control.ini" heads

if ($LASTEXITCODE -ne 0) {
    throw "Control migration head inspection failed."
}

& $python -m alembic -c ".\alembic-control.ini" current

if ($LASTEXITCODE -ne 0) {
    throw "Control database revision inspection failed."
}

Write-Host "PHASE38_2F3B_SAVED_SCOPE_LOADING_GATE_PASSED"