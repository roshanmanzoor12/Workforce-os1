#Requires -Version 5.1

$ErrorActionPreference = "Stop"

$BackendRoot =
    "C:\workforce-os\backend"

$Python =
    "C:\workforce-os\.venv\Scripts\python.exe"

$MigrationScript =
    Join-Path `
        $BackendRoot `
        "scripts\phase09_apply_tenant_migration.ps1"

$LiveVerificationScript =
    Join-Path `
        $BackendRoot `
        "scripts\phase09_verify_live_accumulation.ps1"

Write-Host ""
Write-Host "================================================="
Write-Host " WorkforceOS Phase 09 Final Acceptance"
Write-Host "================================================="
Write-Host ""

Push-Location $BackendRoot

try
{
    Write-Host "[1/5] Compiling Phase 09 integration..."

    & $Python `
        -m py_compile `
        app\modules\work_sessions\live_integration.py `
        app\modules\work_sessions\reconciliation.py `
        app\modules\activity\agent_router.py `
        tests\modules\work_sessions\test_live_integration.py `
        tests\modules\work_sessions\test_activity_router_integration.py `
        tests\modules\work_sessions\test_reconciliation.py

    if ($LASTEXITCODE -ne 0)
    {
        throw "Phase 09 integration compile failed."
    }

    Write-Host "PASS compile"
    Write-Host ""

    Write-Host "[2/5] Running complete work-session tests..."

    & $Python `
        -m pytest `
        tests\modules\work_sessions `
        -v

    if ($LASTEXITCODE -ne 0)
    {
        throw "Phase 09 test suite failed."
    }

    Write-Host "PASS tests"
    Write-Host ""

    Write-Host "[3/5] Verifying tenant migration..."

    & $MigrationScript

    if ($LASTEXITCODE -ne 0)
    {
        throw (
            "Phase 09 migration verification failed."
        )
    }

    Write-Host "PASS migration"
    Write-Host ""

    Write-Host "[4/5] Verifying Activity API remains registered..."

    $OpenApiUrl =
        "http://127.0.0.1:8001/openapi.json"

    try
    {
        $OpenApi =
            Invoke-RestMethod `
                -Uri $OpenApiUrl `
                -Method Get

        $ActivityStatePath =
            $OpenApi.paths.PSObject.Properties.Name |
            Where-Object {
                $_ -eq "/api/v1/device-agent/activity-state"
            }

        if ($null -eq $ActivityStatePath)
        {
            throw (
                "Activity state API missing from OpenAPI."
            )
        }
    }
    catch
    {
        throw (
            "Backend must be running on 127.0.0.1:8001. " +
            $_.Exception.Message
        )
    }

    Write-Host "PASS Activity API registered"
    Write-Host ""

    Write-Host "[5/5] Verifying live work-session accumulation..."

    & $LiveVerificationScript

    if ($LASTEXITCODE -ne 0)
    {
        throw (
            "Live work-session accumulation verification failed."
        )
    }

    Write-Host ""
    Write-Host "================================================="
    Write-Host " PHASE 09 WORK SESSIONS: FINAL ACCEPTANCE PASS"
    Write-Host "================================================="
    Write-Host ""
}
finally
{
    Pop-Location
}