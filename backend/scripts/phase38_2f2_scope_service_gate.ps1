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
    ".\app\modules\workspace_rbac\scope_repository.py"
    ".\app\modules\workspace_rbac\scope_schemas.py"
    ".\app\modules\workspace_rbac\scope_policy.py"
    ".\app\modules\workspace_rbac\scope_resources.py"
    ".\app\modules\workspace_rbac\scope_service.py"
    ".\app\modules\workspace_permissions\saved_scopes.py"
    ".\tests\modules\workspace_permissions\test_phase38_scope_grant_repository.py"
    ".\tests\modules\workspace_permissions\test_phase38_scope_grant_service.py"
    ".\tests\modules\workspace_permissions\test_phase38_saved_scope_resolution.py"
)

foreach ($file in $phase38Files) {
    if (-not (Test-Path -LiteralPath $file)) {
        throw "Required Phase 38.2F2 file is missing: $file"
    }
}

Write-Host "Checking Phase 38.2F2 syntax..."

& $pythonExecutable -m py_compile @phase38Files

if ($LASTEXITCODE -ne 0) {
    throw "Phase 38.2F2 syntax verification failed."
}

Write-Host "Checking scope storage, repository, service, and resolution..."

& $pythonExecutable -m pytest `
    ".\tests\modules\workspace_permissions\test_phase38_scope_grant_storage.py" `
    ".\tests\modules\workspace_permissions\test_phase38_scope_grant_repository.py" `
    ".\tests\modules\workspace_permissions\test_phase38_scope_grant_service.py" `
    ".\tests\modules\workspace_permissions\test_phase38_saved_scope_resolution.py" `
    -q `
    --tb=short `
    --import-mode=importlib `
    --color=no

if ($LASTEXITCODE -ne 0) {
    throw "Phase 38.2F2 scope verification failed."
}

Write-Host "Checking employee, project, permission, and tenant regressions..."

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
    throw "Phase 38.2F2 regression verification failed."
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

Write-Host "PHASE38_2F2_SCOPE_SERVICE_GATE_PASSED"