param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^tenant_[0-9a-fA-F]{32}$')]
    [string]$DatabaseName
)

$ErrorActionPreference = "Stop"

$BackendRoot = "C:\workforce-os\backend"
$Python = "C:\workforce-os\backend\.venv\Scripts\python.exe"
$TenantAlembic = ".\alembic.tenant.ini"
$Migration = ".\migrations\tenant\versions\d3e4f5a6b7c8_add_meetings_domain.py"

Set-Location $BackendRoot

Write-Host "================================================="
Write-Host " WorkforceOS Phase 11.8 Meeting Migration Gate"
Write-Host "================================================="
Write-Host ""
Write-Host "Tenant database: $DatabaseName"
Write-Host ""

# =========================================================
# PREFLIGHT 1/4
# =========================================================

Write-Host "[preflight 1/4] PostgreSQL 5434..."

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

# =========================================================
# PREFLIGHT 2/4
# =========================================================

Write-Host "[preflight 2/4] Tenant Alembic config..."

if (-not (Test-Path $TenantAlembic))
{
    throw "alembic.tenant.ini missing."
}

Write-Host "PASS tenant config"
Write-Host ""

# =========================================================
# PREFLIGHT 3/4
# =========================================================

Write-Host "[preflight 3/4] Migration file..."

if (-not (Test-Path $Migration))
{
    throw "Meeting migration missing."
}

Write-Host "PASS migration file"
Write-Host ""

# =========================================================
# PREFLIGHT 4/4
# =========================================================

Write-Host "[preflight 4/4] Database name contract..."

if ($DatabaseName -notmatch '^tenant_[0-9a-fA-F]{32}$')
{
    throw "Invalid tenant database name."
}

Write-Host "PASS tenant database name"
Write-Host ""

# =========================================================
# 1/7 COMPILE
# =========================================================

Write-Host "[1/7] Compile migration..."

& $Python `
    -m py_compile `
    $Migration

if ($LASTEXITCODE -ne 0)
{
    throw "Migration compile failed."
}

Write-Host "PASS migration compile"
Write-Host ""

# =========================================================
# 2/7 CONTRACT TESTS
# =========================================================

Write-Host "[2/7] Migration contract tests..."

& $Python `
    -m pytest `
    .\tests\test_phase11_8_meeting_migration_contract.py `
    .\tests\test_phase11_8_meeting_model_migration_parity.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Meeting migration tests failed."
}

Write-Host "PASS migration tests"
Write-Host ""

# =========================================================
# 3/7 HEAD
# =========================================================

Write-Host "[3/7] Tenant migration head..."

$Heads = (
    & $Python `
        -m alembic `
        -c $TenantAlembic `
        heads
)

if ($LASTEXITCODE -ne 0)
{
    throw "Tenant heads failed."
}

Write-Host $Heads

if ($Heads -notmatch "d3e4f5a6b7c8")
{
    throw "Meeting migration is not the tenant Alembic head."
}

Write-Host "PASS tenant migration head"
Write-Host ""

# =========================================================
# 4/7 CURRENT BEFORE
# =========================================================

Write-Host "[4/7] Current tenant revision before upgrade..."

$CurrentBefore = (
    & $Python `
        -m alembic `
        -c $TenantAlembic `
        -x "database_name=$DatabaseName" `
        current
)

if ($LASTEXITCODE -ne 0)
{
    throw "Unable to read current tenant revision."
}

Write-Host $CurrentBefore
Write-Host "PASS tenant database reachable"
Write-Host ""

# =========================================================
# 5/7 UPGRADE
# =========================================================

Write-Host "[5/7] Upgrade selected tenant database..."

& $Python `
    -m alembic `
    -c $TenantAlembic `
    -x "database_name=$DatabaseName" `
    upgrade head

if ($LASTEXITCODE -ne 0)
{
    throw "Tenant upgrade failed."
}

Write-Host "PASS tenant upgrade"
Write-Host ""

# =========================================================
# 6/7 CURRENT AFTER
# =========================================================

Write-Host "[6/7] Verify tenant revision after upgrade..."

$CurrentAfter = (
    & $Python `
        -m alembic `
        -c $TenantAlembic `
        -x "database_name=$DatabaseName" `
        current
)

if ($LASTEXITCODE -ne 0)
{
    throw "Tenant current revision check failed."
}

Write-Host $CurrentAfter

if ($CurrentAfter -notmatch "d3e4f5a6b7c8")
{
    throw "Selected tenant database did not reach d3e4f5a6b7c8."
}

Write-Host "PASS tenant current revision"
Write-Host ""

# =========================================================
# 7/7 APPLICATION
# =========================================================

Write-Host "[7/7] Application import..."

& $Python `
    -c "from app.main import app; print('PASS app.main')"

if ($LASTEXITCODE -ne 0)
{
    throw "Application import failed."
}

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 11.8 MEETING MIGRATION: PASS"
Write-Host " Database: $DatabaseName"
Write-Host " Revision: d3e4f5a6b7c8"
Write-Host "================================================="