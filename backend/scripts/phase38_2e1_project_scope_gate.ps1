param(
    [string]$BackendPath = "C:\workforce-os\backend"
)

$ErrorActionPreference = "Stop"

Set-Location -LiteralPath $BackendPath
$env:PYTHONPATH = $BackendPath

$phase38Python = Join-Path $BackendPath ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $phase38Python)) {
    throw "Backend Python executable was not found: $phase38Python"
}

$phase38SourceFiles = @(
    ".\app\modules\projects\access.py"
    ".\app\modules\projects\repository.py"
    ".\app\modules\projects\scoped_service.py"
    ".\app\modules\projects\permissions.py"
    ".\app\modules\projects\router.py"
    ".\tests\modules\projects\test_phase38_project_scope_policy.py"
    ".\tests\modules\projects\test_phase38_project_scoped_service.py"
    ".\tests\modules\projects\test_phase38_project_scoped_repository.py"
    ".\tests\modules\projects\test_phase38_project_scope_routes.py"
)

foreach ($file in $phase38SourceFiles) {
    if (-not (Test-Path -LiteralPath $file)) {
        throw "Required Phase 38.2E1 file missing: $file"
    }
}

Write-Host "Checking Phase 38.2E1 syntax..."

& $phase38Python -m py_compile @phase38SourceFiles

if ($LASTEXITCODE -ne 0) {
    throw "Phase 38.2E1 syntax verification failed."
}

Write-Host "Checking project business behavior and resource scopes..."

& $phase38Python -m pytest `
    ".\tests\modules\projects" `
    ".\tests\modules\workspace_permissions\test_phase25_permission_scopes.py" `
    -q `
    --tb=short `
    --import-mode=importlib `
    --color=no

if ($LASTEXITCODE -ne 0) {
    throw "Phase 38.2E1 project scope verification failed."
}

Write-Host "Checking existing permissions, API keys, and tenant security..."

& $phase38Python -m pytest `
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
    throw "Phase 38.2E1 security regression verification failed."
}

Write-Host "PHASE38_2E1_PROJECT_SCOPE_GATE_PASSED"