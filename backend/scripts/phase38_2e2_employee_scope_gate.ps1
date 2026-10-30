$ErrorActionPreference = "Stop"

$backendRoot = Split-Path -Parent $PSScriptRoot
Set-Location $backendRoot

$env:PYTHONPATH = $backendRoot
$python = Join-Path $backendRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $python)) {
    throw "Backend virtual environment was not found."
}

$sourceFiles = @(
    ".\app\modules\employees\scope_access.py"
    ".\app\modules\employees\scoped_repository.py"
    ".\app\modules\employees\scoped_service.py"
    ".\app\modules\employees\router.py"
    ".\app\modules\employees\access_service.py"
    ".\tests\modules\employees\test_phase38_employee_scope_policy.py"
    ".\tests\modules\employees\test_phase38_employee_scoped_repository.py"
    ".\tests\modules\employees\test_phase38_employee_scoped_service.py"
    ".\tests\modules\employees\test_phase38_employee_scope_routes.py"
)

foreach ($file in $sourceFiles) {
    if (-not (Test-Path -LiteralPath $file)) {
        throw "Required file missing: $file"
    }
}

Write-Host "Checking Phase 38.2E2 syntax..."

& $python -m py_compile @sourceFiles

if ($LASTEXITCODE -ne 0) {
    throw "Phase 38.2E2 syntax verification failed."
}

Write-Host "Checking employee permission and resource scopes..."

& $python -m pytest `
    ".\tests\modules\employees" `
    -q `
    --tb=short `
    --import-mode=importlib `
    --color=no

if ($LASTEXITCODE -ne 0) {
    throw "Phase 38.2E2 employee scope verification failed."
}

Write-Host "Checking project, permission, API key, and tenant regressions..."

& $python -m pytest `
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
    throw "Phase 38.2E2 regression verification failed."
}

Write-Host "PHASE38_2E2_EMPLOYEE_SCOPE_GATE_PASSED"