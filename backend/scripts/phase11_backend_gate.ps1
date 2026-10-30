#Requires -Version 5.1

$ErrorActionPreference = "Stop"

$BackendRoot = "C:\workforce-os\backend"
$Python = "C:\workforce-os\.venv\Scripts\python.exe"

Set-Location $BackendRoot

Write-Host ""
Write-Host "==============================================="
Write-Host " WorkforceOS Phase 11 Backend Gate"
Write-Host "==============================================="
Write-Host ""

$WebsiteTrackingFiles = @(
    "app\modules\website_tracking\__init__.py",
    "app\modules\website_tracking\models.py",
    "app\modules\website_tracking\schemas.py",
    "app\modules\website_tracking\privacy.py",
    "app\modules\website_tracking\repository.py",
    "app\modules\website_tracking\service.py",
    "app\modules\website_tracking\coordinator.py",
    "app\modules\website_tracking\status_schemas.py",
    "app\modules\website_tracking\query_service.py",
    "app\modules\website_tracking\history_schemas.py",
    "app\modules\website_tracking\history_service.py",
    "app\modules\website_tracking\agent_router.py",
    "app\modules\website_tracking\status_router.py",
    "app\modules\website_tracking\agent_history_router.py",
    "app\modules\website_tracking\website_tracking_api_router.py",
    "migrations\tenant\versions\c2d3e4f5a6b7_add_website_tracking.py"
)

Write-Host "[1/4] Compile Website Tracking module..."

foreach ($File in $WebsiteTrackingFiles)
{
    if (-not (Test-Path $File))
    {
        throw (
            "Required Phase 11 file missing: " +
            $File
        )
    }

    & $Python `
        -m py_compile `
        $File

    if ($LASTEXITCODE -ne 0)
    {
        throw (
            "Phase 11 compile failed: " +
            $File
        )
    }
}

Write-Host "PASS Website Tracking compile"
Write-Host ""

Write-Host "[2/4] Privacy tests..."

& $Python `
    -m pytest `
    tests\modules\website_tracking\test_privacy.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Phase 11 privacy tests failed."
}

Write-Host "PASS privacy tests"
Write-Host ""

Write-Host "[3/4] Schema tests..."

& $Python `
    -m pytest `
    tests\modules\website_tracking\test_schemas.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Phase 11 schema tests failed."
}

Write-Host "PASS schema tests"
Write-Host ""

Write-Host "[4/4] API contract tests..."

& $Python `
    -m pytest `
    tests\modules\website_tracking\test_api_contract.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Phase 11 API contract tests failed."
}

Write-Host "PASS API contract tests"

Write-Host ""
Write-Host "==============================================="
Write-Host " PHASE 11 BACKEND GATE: PASS"
Write-Host "==============================================="
Write-Host ""