#Requires -Version 5.1

$ErrorActionPreference = "Stop"

$BackendDirectory =
    Split-Path `
        -Parent `
        $PSScriptRoot

$Python =
    "C:\workforce-os\.venv\Scripts\python.exe"

Write-Host ""
Write-Host "============================================="
Write-Host " WorkforceOS Phase 08 Backend Test Suite"
Write-Host "============================================="
Write-Host ""

if (-not (Test-Path $Python))
{
    throw (
        "WorkforceOS virtual environment Python not found: " +
        $Python
    )
}

Push-Location $BackendDirectory

try
{
    Write-Host "Compiling activity module..."
    Write-Host ""

    & $Python `
        -m py_compile `
        .\app\modules\activity\models.py `
        .\app\modules\activity\schemas.py `
        .\app\modules\activity\repository.py `
        .\app\modules\activity\service.py `
        .\app\modules\activity\agent_router.py `
        .\app\modules\activity\activity_api_router.py `
        .\migrations\tenant\versions\f8a1c3d4e5b6_add_activity_state_events.py

    if ($LASTEXITCODE -ne 0)
    {
        throw (
            "Phase 08 activity compile failed."
        )
    }

    Write-Host ""
    Write-Host "Compile passed."
    Write-Host ""

    Write-Host "Running activity tests..."
    Write-Host ""

    & $Python `
        -m pytest `
        .\tests\modules\activity\test_activity_api_contract.py `
        .\tests\modules\activity\test_activity_schemas.py `
        .\tests\modules\activity\test_activity_models.py `
        .\tests\modules\activity\test_activity_repository.py `
        .\tests\modules\activity\test_activity_migration.py `
        -q

    if ($LASTEXITCODE -ne 0)
    {
        throw (
            "Phase 08 activity tests failed."
        )
    }

    Write-Host ""
    Write-Host "============================================="
    Write-Host " PHASE 08 BACKEND TEST SUITE: PASS"
    Write-Host "============================================="
    Write-Host ""
}
finally
{
    Pop-Location
}