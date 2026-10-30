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
Write-Host " WorkforceOS Phase 12.2 Attendance Timeline Gate"
Write-Host "================================================="
Write-Host ""
Write-Host "Tenant: $DatabaseName"
Write-Host ""

$Required = @(
    ".\app\modules\timeline\enums.py",
    ".\app\modules\timeline\presenters.py",
    ".\app\modules\timeline\sources.py",
    ".\app\modules\timeline\registry.py",
    ".\app\modules\timeline\service.py",
    ".\app\modules\timeline\router.py",
    ".\tests\test_phase12_timeline_foundation.py",
    ".\tests\test_phase12_2_attendance_timeline_contract.py",
    ".\tests\test_phase12_2_timeline_source_registry.py",
    ".\tests\test_phase12_2_timeline_privacy_contract.py"
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

# =========================================================
# 1/7 COMPILE
# =========================================================

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

# =========================================================
# 2/7 APP IMPORT
# =========================================================

Write-Host "[2/7] Application import..."

& $Python `
    -c "from app.main import app; print('PASS app.main')"

if ($LASTEXITCODE -ne 0)
{
    throw "Application import failed."
}

Write-Host ""

# =========================================================
# 3/7 FOUNDATION REGRESSION
# =========================================================

Write-Host "[3/7] Timeline foundation regression..."

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

# =========================================================
# 4/7 ATTENDANCE CONTRACT
# =========================================================

Write-Host "[4/7] Attendance timeline contract..."

& $Python `
    -m pytest `
    .\tests\test_phase12_2_attendance_timeline_contract.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Attendance timeline contract failed."
}

Write-Host "PASS attendance contract"
Write-Host ""

# =========================================================
# 5/7 SOURCE REGISTRY + PRIVACY
# =========================================================

Write-Host "[5/7] Registry and privacy..."

& $Python `
    -m pytest `
    .\tests\test_phase12_2_timeline_source_registry.py `
    .\tests\test_phase12_2_timeline_privacy_contract.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Timeline registry/privacy tests failed."
}

Write-Host "PASS registry/privacy"
Write-Host ""

# =========================================================
# 6/7 TENANT REVISION
# =========================================================

Write-Host "[6/7] Tenant schema revision..."

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

# =========================================================
# 7/7 OPENAPI
# =========================================================

Write-Host "[7/7] Timeline OpenAPI..."

$OpenAPICheck = @'
from app.main import app

schema = app.openapi()

path = (
    "/api/v1/workspaces/"
    "{workspace_id}/timeline/me"
)

if path not in schema["paths"]:
    raise SystemExit(
        "Timeline self route missing."
    )

operation = schema["paths"][path]["get"]

parameters = {
    item["name"]
    for item in operation.get(
        "parameters",
        []
    )
}

required = {
    "source",
    "event_type",
    "before",
    "after",
    "limit",
    "cursor",
}

missing = required - parameters

if missing:
    raise SystemExit(
        "Missing timeline parameters: "
        + str(sorted(missing))
    )

print("PASS timeline OpenAPI")
'@

$OpenAPICheck | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Timeline OpenAPI check failed."
}

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 12.2 ATTENDANCE TIMELINE: PASS"
Write-Host "================================================="
Write-Host ""
Write-Host "Goals source:          PASS"
Write-Host "Notes source:          PASS"
Write-Host "Knowledge source:      PASS"
Write-Host "Meetings source:       PASS"
Write-Host "Attendance source:     PASS"
Write-Host "Attendance privacy:    PASS"
Write-Host "Source filtering:      PASS"
Write-Host "Cursor pagination:     PASS"
Write-Host "Tenant schema:         $ExpectedTenantHead"
Write-Host "Migration required:    NO"
Write-Host "================================================="