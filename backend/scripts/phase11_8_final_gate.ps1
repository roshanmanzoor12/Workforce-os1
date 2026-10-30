$ErrorActionPreference = "Stop"

$BackendRoot = "C:\workforce-os\backend"
$Python = "C:\workforce-os\backend\.venv\Scripts\python.exe"

Set-Location $BackendRoot

Write-Host "================================================="
Write-Host " WorkforceOS Phase 11.8 FINAL Certification"
Write-Host "================================================="
Write-Host ""

Write-Host "[preflight 1/3] PostgreSQL..."

$Postgres = Test-NetConnection `
    -ComputerName "127.0.0.1" `
    -Port 5434 `
    -WarningAction SilentlyContinue

if (-not $Postgres.TcpTestSucceeded)
{
    throw "PostgreSQL unavailable."
}

Write-Host "PASS PostgreSQL"
Write-Host ""

Write-Host "[preflight 2/3] Application..."

& $Python `
    -c "from app.main import app; print('PASS app.main')"

if ($LASTEXITCODE -ne 0)
{
    throw "Application import failed."
}

Write-Host ""

Write-Host "[preflight 3/3] Tenant migration head..."

$Head = (
    & $Python `
        -m alembic `
        -c .\alembic.tenant.ini `
        heads
)

if ($LASTEXITCODE -ne 0)
{
    throw "Tenant heads failed."
}

Write-Host $Head

if ($Head -notmatch "d3e4f5a6b7c8")
{
    throw "Meeting revision is not tenant head."
}

Write-Host "PASS tenant head"
Write-Host ""

Write-Host "[1/5] Meeting migration..."

.\scripts\phase11_8_meeting_migration_gate.ps1

if ($LASTEXITCODE -ne 0)
{
    throw "Meeting migration gate failed."
}

Write-Host ""

Write-Host "[2/5] Tenant schema..."

.\scripts\phase11_8_tenant_schema_db_probe.ps1

if ($LASTEXITCODE -ne 0)
{
    throw "Tenant schema DB probe failed."
}

Write-Host ""

Write-Host "[3/5] Integration..."

.\scripts\phase11_8_integration_gate.ps1

if ($LASTEXITCODE -ne 0)
{
    throw "Integration gate failed."
}

Write-Host ""

Write-Host "[4/5] Full regression..."

.\scripts\phase11_8_full_regression_gate.ps1

if ($LASTEXITCODE -ne 0)
{
    throw "Full regression failed."
}

Write-Host ""

Write-Host "[5/5] Final tenant revision..."

$Current = (
    & $Python `
        -m alembic `
        -c .\alembic.tenant.ini `
        current
)

if ($LASTEXITCODE -ne 0)
{
    throw "Unable to read tenant current revision."
}

Write-Host $Current

if ($Current -notmatch "d3e4f5a6b7c8")
{
    throw "Tenant DB is not at Phase 11.8 head."
}

Write-Host "PASS final tenant revision"

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 11.8: PASS"
Write-Host " Permissions / Meetings / Monitoring Control"
Write-Host "================================================="