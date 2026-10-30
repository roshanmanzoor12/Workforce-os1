$ErrorActionPreference = "Stop"

$BackendRoot = "C:\workforce-os\backend"
$Python = "C:\workforce-os\backend\.venv\Scripts\python.exe"

Set-Location $BackendRoot

Write-Host "================================================="
Write-Host " WorkforceOS Phase 12.1 Timeline Query Gate"
Write-Host "================================================="
Write-Host ""

$Required = @(
    ".\app\modules\timeline\cursor.py",
    ".\app\modules\timeline\filters.py",
    ".\app\modules\timeline\registry.py",
    ".\app\modules\timeline\schemas.py",
    ".\app\modules\timeline\service.py",
    ".\app\modules\timeline\router.py",
    ".\tests\test_phase12_1_timeline_cursor.py",
    ".\tests\test_phase12_1_timeline_query_contract.py"
)

Write-Host "[preflight] Required files..."

foreach ($Path in $Required)
{
    if (-not (Test-Path $Path))
    {
        throw "Missing required file: $Path"
    }
}

Write-Host "PASS required files"
Write-Host ""

Write-Host "[1/6] Compile timeline query layer..."

& $Python `
    -m compileall `
    .\app\modules\timeline `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Timeline query compile failed."
}

Write-Host "PASS compile"
Write-Host ""

Write-Host "[2/6] Application import..."

& $Python `
    -c "from app.main import app; print('PASS app.main')"

if ($LASTEXITCODE -ne 0)
{
    throw "Application import failed."
}

Write-Host ""

Write-Host "[3/6] Foundation regression..."

& $Python `
    -m pytest `
    .\tests\test_phase12_timeline_foundation.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Timeline foundation regression failed."
}

Write-Host "PASS foundation regression"
Write-Host ""

Write-Host "[4/6] Cursor tests..."

& $Python `
    -m pytest `
    .\tests\test_phase12_1_timeline_cursor.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Timeline cursor tests failed."
}

Write-Host "PASS cursor"
Write-Host ""

Write-Host "[5/6] Query contract tests..."

& $Python `
    -m pytest `
    .\tests\test_phase12_1_timeline_query_contract.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Timeline query contract failed."
}

Write-Host "PASS query contract"
Write-Host ""

Write-Host "[6/6] Tenant schema unchanged..."

$Head = (
    & $Python `
        -m alembic `
        -c .\alembic.tenant.ini `
        heads
)

if ($LASTEXITCODE -ne 0)
{
    throw "Unable to read tenant migration head."
}

Write-Host $Head

if (
    $Head -notmatch "f6a7b8c9d0e1"
)
{
    throw "Unexpected tenant schema head."
}

Write-Host "PASS schema unchanged"
Write-Host ""

Write-Host "================================================="
Write-Host " PHASE 12.1 TIMELINE QUERY LAYER: PASS"
Write-Host "================================================="
Write-Host ""
Write-Host "Source filtering:     PASS"
Write-Host "Event filtering:      PASS"
Write-Host "Date filtering:       PASS"
Write-Host "Cursor pagination:    PASS"
Write-Host "Self timeline:        PASS"
Write-Host "Admin employee view:  PASS"
Write-Host "Schema migration:     NOT REQUIRED"