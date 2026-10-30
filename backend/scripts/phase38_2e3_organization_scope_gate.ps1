$ErrorActionPreference = "Stop"

$backendRoot = Split-Path -Parent $PSScriptRoot

Set-Location -LiteralPath $backendRoot

$env:PYTHONPATH = $backendRoot

$pythonExecutable = Join-Path `
    $backendRoot `
    ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $pythonExecutable)) {
    throw "Backend Python executable was not found."
}

$sourceFiles = @(
    ".\app\modules\employees\organization_policy.py"
    ".\app\modules\employees\organization_repository.py"
    ".\app\modules\employees\organization_service.py"
    ".\app\modules\employees\router.py"
    ".\app\modules\employees\access_service.py"
    ".\tests\modules\employees\test_phase38_organization_policy.py"
    ".\tests\modules\employees\test_phase38_organization_repository.py"
    ".\tests\modules\employees\test_phase38_organization_service.py"
    ".\tests\modules\employees\test_phase38_organization_routes.py"
)

foreach ($sourceFile in $sourceFiles) {
    if (-not (Test-Path -LiteralPath $sourceFile)) {
        throw "Required Phase 38.2E3 file is missing: $sourceFile"
    }
}

Write-Host "Checking Phase 38.2E3 syntax..."

& $pythonExecutable -m py_compile @sourceFiles

if ($LASTEXITCODE -ne 0) {
    throw "Phase 38.2E3 syntax verification failed."
}

Write-Host "Checking department and team authorization..."

& $pythonExecutable -m pytest `
    ".\tests\modules\employees\test_phase38_organization_policy.py" `
    ".\tests\modules\employees\test_phase38_organization_repository.py" `
    ".\tests\modules\employees\test_phase38_organization_service.py" `
    ".\tests\modules\employees\test_phase38_organization_routes.py" `
    -q `
    --tb=short `
    --import-mode=importlib `
    --color=no

if ($LASTEXITCODE -ne 0) {
    throw "Phase 38.2E3 organization authorization verification failed."
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
    throw "Phase 38.2E3 regression verification failed."
}

Write-Host "PHASE38_2E3_ORGANIZATION_SCOPE_GATE_PASSED"