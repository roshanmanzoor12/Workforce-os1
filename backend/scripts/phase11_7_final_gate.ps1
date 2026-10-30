$ErrorActionPreference = "Stop"

$BackendRoot = "C:\workforce-os\backend"
$Python = "C:\workforce-os\backend\.venv\Scripts\python.exe"

Set-Location $BackendRoot

Write-Host "================================================="
Write-Host " WorkforceOS Phase 11.7 FINAL Certification"
Write-Host "================================================="
Write-Host ""

Write-Host "[preflight 1/3] PostgreSQL 5434..."

$Postgres = Test-NetConnection `
    -ComputerName "127.0.0.1" `
    -Port 5434 `
    -WarningAction SilentlyContinue

if (-not $Postgres.TcpTestSucceeded)
{
    throw "PostgreSQL 5434 is not reachable."
}

Write-Host "PASS PostgreSQL reachable"
Write-Host ""

Write-Host "[preflight 2/3] Control migration..."

$Revision = (
    & $Python `
        -m alembic `
        -c .\alembic-control.ini `
        current
)

if ($LASTEXITCODE -ne 0)
{
    throw "Alembic current failed."
}

Write-Host $Revision

if ($Revision -notmatch "d9e0f1a2b3c4")
{
    throw "Phase 11.7 control revision missing."
}

Write-Host "PASS control revision"
Write-Host ""

Write-Host "[preflight 3/3] Application import..."

& $Python `
    -c "from app.main import app; print('PASS app.main import')"

if ($LASTEXITCODE -ne 0)
{
    throw "Application import failed."
}

Write-Host ""

Write-Host "[1/6] Compile final Phase 11.7..."

& $Python `
    -m compileall `
    .\app\modules\memberships `
    .\app\modules\employees `
    .\app\modules\attendance `
    .\app\modules\tenant_api `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Phase 11.7 compile failed."
}

Write-Host "PASS compile"
Write-Host ""

Write-Host "[2/6] Final model contract..."

& $Python `
    -m pytest `
    .\tests\test_phase11_7_final_model_contract.py `
    .\tests\test_phase11_7_final_attendance_contract.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Final model contract failed."
}

Write-Host "PASS model contract"
Write-Host ""

Write-Host "[3/6] Final security contract..."

& $Python `
    -m pytest `
    .\tests\test_phase11_7_final_security_contract.py `
    .\tests\test_phase11_7_final_privacy_contract.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Final security contract failed."
}

Write-Host "PASS security contract"
Write-Host ""

Write-Host "[4/6] Final OpenAPI contract..."

& $Python `
    -m pytest `
    .\tests\test_phase11_7_final_openapi_contract.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Final OpenAPI contract failed."
}

Write-Host "PASS OpenAPI contract"
Write-Host ""

Write-Host "[5/6] Tenant schema metadata..."

.\scripts\phase11_7_schema_contract_probe.ps1

if ($LASTEXITCODE -ne 0)
{
    throw "Schema contract probe failed."
}

Write-Host ""

Write-Host "[6/6] Regression suite..."

.\scripts\phase11_7_final_regression_gate.ps1

if ($LASTEXITCODE -ne 0)
{
    throw "Phase 11.7 regression suite failed."
}

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 11.7: PASS"
Write-Host " Membership / Employee / Department / Team /"
Write-Host " Attendance / Authorized Tenant REST"
Write-Host "================================================="