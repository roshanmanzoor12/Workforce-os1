param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^tenant_[0-9a-fA-F]{32}$')]
    [string]$DatabaseName
)

$ErrorActionPreference = "Stop"

$BackendRoot = "C:\workforce-os\backend"
$Python = "C:\workforce-os\backend\.venv\Scripts\python.exe"

Set-Location $BackendRoot

Write-Host "================================================="
Write-Host " WorkforceOS Tenant Database Verification"
Write-Host "================================================="
Write-Host ""
Write-Host "Database: $DatabaseName"
Write-Host ""

Write-Host "[1/3] PostgreSQL 5434..."

$Postgres = Test-NetConnection `
    -ComputerName "127.0.0.1" `
    -Port 5434 `
    -WarningAction SilentlyContinue

if (-not $Postgres.TcpTestSucceeded)
{
    throw "PostgreSQL 5434 is unreachable."
}

Write-Host "PASS PostgreSQL reachable"
Write-Host ""

Write-Host "[2/3] Tenant database connection..."

$Current = (
    & $Python `
        -m alembic `
        -c .\alembic.tenant.ini `
        -x "database_name=$DatabaseName" `
        current 2>&1
)

$ExitCode = $LASTEXITCODE

if ($ExitCode -ne 0)
{
    $Text = $Current | Out-String

    Write-Host $Text

    if ($Text -match "InvalidCatalogNameError")
    {
        throw "Tenant database '$DatabaseName' does not exist."
    }

    throw "Unable to connect to tenant database."
}

Write-Host $Current
Write-Host "PASS tenant database exists"
Write-Host ""

Write-Host "[3/3] Alembic tenant head..."

$Head = (
    & $Python `
        -m alembic `
        -c .\alembic.tenant.ini `
        heads
)

if ($LASTEXITCODE -ne 0)
{
    throw "Unable to read tenant Alembic head."
}

Write-Host $Head

if ($Head -notmatch "d3e4f5a6b7c8")
{
    throw "Expected tenant head d3e4f5a6b7c8 was not found."
}

Write-Host "PASS tenant migration head"
Write-Host ""

Write-Host "================================================="
Write-Host " TENANT DATABASE VERIFICATION: PASS"
Write-Host "================================================="
