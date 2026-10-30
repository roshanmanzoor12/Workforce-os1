$ErrorActionPreference = "Stop"

$BackendRoot = "C:\workforce-os\backend"
$Python = "C:\workforce-os\backend\.venv\Scripts\python.exe"

Set-Location $BackendRoot

Write-Host "================================================="
Write-Host " WorkforceOS Phase 12 Timeline Foundation Gate"
Write-Host "================================================="
Write-Host ""

$Required = @(
    ".\app\modules\timeline\enums.py",
    ".\app\modules\timeline\schemas.py",
    ".\app\modules\timeline\sources.py",
    ".\app\modules\timeline\service.py",
    ".\app\modules\timeline\router.py",
    ".\tests\test_phase12_timeline_foundation.py"
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

Write-Host "[1/6] Compile timeline..."

& $Python `
    -m compileall `
    .\app\modules\timeline `
    .\app\modules\workspace_permissions `
    .\app\modules\tenant_api `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Timeline compile failed."
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

Write-Host "[3/6] Timeline tests..."

& $Python `
    -m pytest `
    .\tests\test_phase12_timeline_foundation.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Timeline foundation tests failed."
}

Write-Host "PASS timeline tests"
Write-Host ""

Write-Host "[4/6] Phase 11.9 regression..."

& $Python `
    -m pytest `
    .\tests\test_phase11_9_ai_productivity_foundation.py `
    .\tests\test_phase11_9_ai_security_contract.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Phase 11.9 regression failed."
}

Write-Host "PASS previous phase regression"
Write-Host ""

Write-Host "[5/6] Tenant migration head..."

$Head = (
    & $Python `
        -m alembic `
        -c .\alembic.tenant.ini `
        heads
)

if ($LASTEXITCODE -ne 0)
{
    throw "Unable to read tenant head."
}

Write-Host $Head

if (
    $Head -notmatch
    "f6a7b8c9d0e1"
)
{
    throw "Unexpected tenant migration head."
}

Write-Host "PASS schema unchanged"
Write-Host ""

Write-Host "[6/6] OpenAPI contract..."

$Check = @'
from app.main import app

paths = app.openapi()["paths"]

required = [
    "/api/v1/workspaces/{workspace_id}/timeline/capabilities",
    "/api/v1/workspaces/{workspace_id}/timeline/me",
    "/api/v1/workspaces/{workspace_id}/timeline/employees/{employee_id}",
]

for path in required:
    if path not in paths:
        raise SystemExit(
            "Missing timeline route: "
            + path
        )

print("PASS timeline OpenAPI")
'@

$Check | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Timeline OpenAPI contract failed."
}

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 12 TIMELINE FOUNDATION: PASS"
Write-Host "================================================="
Write-Host ""
Write-Host "Sources:"
Write-Host " Goals:       PASS"
Write-Host " Notes:       PASS"
Write-Host " Knowledge:   PASS"
Write-Host " Meetings:    PASS"
Write-Host ""
Write-Host "Attendance/activity sources: NEXT"