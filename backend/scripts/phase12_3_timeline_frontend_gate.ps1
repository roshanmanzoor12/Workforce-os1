param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^tenant_[0-9a-fA-F]{32}$')]
    [string]$DatabaseName
)

$ErrorActionPreference = "Stop"

$BackendRoot = "C:\workforce-os\backend"
$Python = "C:\workforce-os\backend\.venv\Scripts\python.exe"
$ExpectedTenantHead = "f6a7b8c9d0e1"

Set-Location $BackendRoot

Write-Host "================================================="
Write-Host " WorkforceOS Phase 12.3 Timeline Frontend Gate"
Write-Host "================================================="
Write-Host ""
Write-Host "Tenant: $DatabaseName"
Write-Host ""

$Required = @(
    ".\app\modules\timeline\query.py",
    ".\app\modules\timeline\security.py",
    ".\app\modules\timeline\factory.py",
    ".\app\modules\timeline\schemas.py",
    ".\app\modules\timeline\service.py",
    ".\app\modules\timeline\router.py",
    ".\app\modules\timeline\__init__.py",
    ".\tests\test_phase12_3_timeline_security.py",
    ".\tests\test_phase12_3_timeline_frontend_contract.py"
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

Write-Host "[1/7] Compile timeline..."

& $Python `
    -m compileall `
    .\app\modules\timeline `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Timeline compile failed."
}

Write-Host "PASS compile"
Write-Host ""

Write-Host "[2/7] Application import..."

& $Python `
    -c "from app.main import app; print('PASS app.main')"

if ($LASTEXITCODE -ne 0)
{
    throw "Application import failed."
}

Write-Host ""

Write-Host "[3/7] Security tests..."

& $Python `
    -m pytest `
    .\tests\test_phase12_3_timeline_security.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Timeline security tests failed."
}

Write-Host "PASS security"
Write-Host ""

Write-Host "[4/7] Frontend contract..."

& $Python `
    -m pytest `
    .\tests\test_phase12_3_timeline_frontend_contract.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Timeline frontend contract failed."
}

Write-Host "PASS frontend contract"
Write-Host ""

Write-Host "[5/7] Phase 12 regressions..."

& $Python `
    -m pytest `
    .\tests\test_phase12_timeline_foundation.py `
    .\tests\test_phase12_1_timeline_cursor.py `
    .\tests\test_phase12_1_timeline_query_contract.py `
    .\tests\test_phase12_2_attendance_timeline_contract.py `
    .\tests\test_phase12_2_timeline_source_registry.py `
    .\tests\test_phase12_2_timeline_privacy_contract.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Phase 12 regression failed."
}

Write-Host "PASS Phase 12 regression"
Write-Host ""

Write-Host "[6/7] Tenant schema..."

$Current = (
    & $Python `
        -m alembic `
        -c .\alembic.tenant.ini `
        -x "database_name=$DatabaseName" `
        current
)

if ($LASTEXITCODE -ne 0)
{
    throw "Unable to read tenant revision."
}

Write-Host $Current

if ($Current -notmatch $ExpectedTenantHead)
{
    throw "Unexpected tenant schema revision."
}

Write-Host "PASS tenant schema"
Write-Host ""

Write-Host "[7/7] Browser safety contract..."

$SafetyCheck = @'
from app.main import app

schema = app.openapi()

timeline_paths = {
    path: value
    for path, value
    in schema["paths"].items()
    if "/timeline" in path
}

text = str(timeline_paths).lower()

for forbidden in [
    "database_name",
    "database_url",
    "tenant_password",
    "device_secret",
    "x-device-secret",
]:
    if forbidden in text:
        raise SystemExit(
            "Forbidden timeline API field: "
            + forbidden
        )

print("PASS browser safety")
'@

$SafetyCheck | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Browser safety contract failed."
}

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 12.3 TIMELINE FRONTEND CONTRACT: PASS"
Write-Host "================================================="
Write-Host ""
Write-Host "Cursor pagination:      PASS"
Write-Host "Source filtering:       PASS"
Write-Host "Event filtering:        PASS"
Write-Host "Date filtering:         PASS"
Write-Host "Applied filters:        PASS"
Write-Host "Metadata sanitization:  PASS"
Write-Host "Browser secret safety:  PASS"
Write-Host "Attendance regression:  PASS"
Write-Host "Tenant schema:          $ExpectedTenantHead"
Write-Host "Migration required:     NO"
Write-Host "================================================="