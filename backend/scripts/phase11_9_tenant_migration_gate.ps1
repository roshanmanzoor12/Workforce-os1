param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^tenant_[0-9a-fA-F]{32}$')]
    [string]$DatabaseName
)

$ErrorActionPreference = "Stop"

$BackendRoot = "C:\workforce-os\backend"
$Python = "C:\workforce-os\backend\.venv\Scripts\python.exe"
$AlembicConfig = ".\alembic.tenant.ini"

Set-Location $BackendRoot

Write-Host "================================================="
Write-Host " WorkforceOS Phase 11.9 Tenant Migration Gate"
Write-Host "================================================="
Write-Host ""
Write-Host "Database: $DatabaseName"
Write-Host ""

Write-Host "[preflight 1/3] PostgreSQL 5434..."

$Postgres = Test-NetConnection `
    -ComputerName "127.0.0.1" `
    -Port 5434 `
    -WarningAction SilentlyContinue

if (-not $Postgres.TcpTestSucceeded)
{
    throw "PostgreSQL 5434 unreachable."
}

Write-Host "PASS PostgreSQL"
Write-Host ""

Write-Host "[preflight 2/3] Alembic config..."

if (-not (Test-Path $AlembicConfig))
{
    throw "Tenant Alembic config missing."
}

Write-Host "PASS tenant config"
Write-Host ""

Write-Host "[preflight 3/3] Migration files..."

$Migrations = @(
    ".\migrations\tenant\versions\e4f5a6b7c8d9_add_goals_and_notes.py",
    ".\migrations\tenant\versions\f6a7b8c9d0e1_add_knowledge_entries.py"
)

foreach ($Migration in $Migrations)
{
    if (-not (Test-Path $Migration))
    {
        throw "Missing migration: $Migration"
    }
}

Write-Host "PASS migrations"
Write-Host ""

Write-Host "[1/7] Compile migrations..."

foreach ($Migration in $Migrations)
{
    & $Python `
        -m py_compile `
        $Migration

    if ($LASTEXITCODE -ne 0)
    {
        throw "Migration compile failed."
    }
}

Write-Host "PASS migration compile"
Write-Host ""

Write-Host "[2/7] Migration contract tests..."

& $Python `
    -m pytest `
    .\tests\test_phase11_9_goals_notes_migration_contract.py `
    .\tests\test_phase11_9_knowledge_migration_contract.py `
    .\tests\test_phase11_9_model_migration_parity.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Phase 11.9 migration tests failed."
}

Write-Host "PASS migration contracts"
Write-Host ""

Write-Host "[3/7] Verify tenant head..."

$Head = (
    & $Python `
        -m alembic `
        -c $AlembicConfig `
        heads
)

if ($LASTEXITCODE -ne 0)
{
    throw "Unable to read tenant heads."
}

Write-Host $Head

if ($Head -notmatch "f6a7b8c9d0e1")
{
    throw "Phase 11.9 migration is not tenant head."
}

Write-Host "PASS tenant head"
Write-Host ""

Write-Host "[4/7] Current tenant revision..."

$CurrentBefore = (
    & $Python `
        -m alembic `
        -c $AlembicConfig `
        -x "database_name=$DatabaseName" `
        current
)

if ($LASTEXITCODE -ne 0)
{
    throw "Unable to read tenant current revision."
}

Write-Host $CurrentBefore
Write-Host "PASS tenant reachable"
Write-Host ""

Write-Host "[5/7] Upgrade tenant to head..."

& $Python `
    -m alembic `
    -c $AlembicConfig `
    -x "database_name=$DatabaseName" `
    upgrade head

if ($LASTEXITCODE -ne 0)
{
    throw "Phase 11.9 tenant upgrade failed."
}

Write-Host "PASS tenant upgrade"
Write-Host ""

Write-Host "[6/7] Verify final revision..."

$CurrentAfter = (
    & $Python `
        -m alembic `
        -c $AlembicConfig `
        -x "database_name=$DatabaseName" `
        current
)

if ($LASTEXITCODE -ne 0)
{
    throw "Final tenant revision check failed."
}

Write-Host $CurrentAfter

if (
    $CurrentAfter -notmatch
    "f6a7b8c9d0e1"
)
{
    throw "Tenant did not reach Phase 11.9 head."
}

Write-Host "PASS final revision"
Write-Host ""

Write-Host "[7/7] Application import..."

& $Python `
    -c "from app.main import app; print('PASS app.main')"

if ($LASTEXITCODE -ne 0)
{
    throw "Application import failed."
}

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 11.9 TENANT MIGRATION: PASS"
Write-Host " Revision: f6a7b8c9d0e1"
Write-Host "================================================="