#Requires -Version 5.1

$ErrorActionPreference = "Stop"

$BackendRoot =
    "C:\workforce-os\backend"

$Python =
    "C:\workforce-os\.venv\Scripts\python.exe"

$MigrationScript =
    Join-Path `
        $BackendRoot `
        "scripts\phase10_apply_tenant_migration.ps1"

$LiveScript =
    Join-Path `
        $BackendRoot `
        "scripts\phase10_verify_live_app_tracking.ps1"

Write-Host ""
Write-Host "================================================="
Write-Host " WorkforceOS Phase 10 Final Acceptance"
Write-Host "================================================="
Write-Host ""

Push-Location $BackendRoot

try
{
    Write-Host "[1/4] Running App Tracking backend tests..."

    & $Python `
        -m pytest `
        tests\modules\app_tracking `
        -v

    if ($LASTEXITCODE -ne 0)
    {
        throw "Phase 10 backend tests failed."
    }

    Write-Host "PASS backend tests"
    Write-Host ""

    Write-Host "[2/4] Verifying tenant migration..."

    & $MigrationScript

    if ($LASTEXITCODE -ne 0)
    {
        throw "Phase 10 tenant migration failed."
    }

    Write-Host "PASS tenant migration"
    Write-Host ""

    Write-Host "[3/4] Verifying backend API registration..."

    $OpenApi =
        Invoke-RestMethod `
            -Uri "http://127.0.0.1:8001/openapi.json" `
            -Method Get

    $Route =
        $OpenApi.paths.PSObject.Properties.Name |
        Where-Object {
            $_ -eq "/api/v1/device-agent/app-observation"
        }

    if ($null -eq $Route)
    {
        throw (
            "App observation API is not registered in running backend."
        )
    }

    Write-Host "PASS App Tracking API registered"
    Write-Host ""

    Write-Host "[4/4] Verifying live App Tracking persistence..."

    & $LiveScript

    if ($LASTEXITCODE -ne 0)
    {
        throw "Phase 10 live App Tracking verification failed."
    }

    Write-Host ""
    Write-Host "================================================="
    Write-Host " PHASE 10 APP TRACKING: FINAL ACCEPTANCE PASS"
    Write-Host "================================================="
}
finally
{
    Pop-Location
}