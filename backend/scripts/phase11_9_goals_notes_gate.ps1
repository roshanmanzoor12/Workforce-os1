$ErrorActionPreference = "Stop"

$BackendRoot = "C:\workforce-os\backend"
$Python = "C:\workforce-os\backend\.venv\Scripts\python.exe"

Set-Location $BackendRoot

Write-Host "================================================="
Write-Host " WorkforceOS Phase 11.9 Goals + Notes Gate"
Write-Host "================================================="
Write-Host ""

$Required = @(
    ".\app\modules\goals\enums.py",
    ".\app\modules\goals\models.py",
    ".\app\modules\goals\schemas.py",
    ".\app\modules\goals\repository.py",
    ".\app\modules\goals\service.py",
    ".\app\modules\goals\self_service.py",
    ".\app\modules\goals\router.py",
    ".\app\modules\notes\models.py",
    ".\app\modules\notes\schemas.py",
    ".\app\modules\notes\repository.py",
    ".\app\modules\notes\service.py",
    ".\app\modules\notes\self_service.py",
    ".\app\modules\notes\router.py",
    ".\migrations\tenant\versions\e4f5a6b7c8d9_add_goals_and_notes.py"
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

Write-Host "[1/6] Compile Phase 11.9 modules..."

& $Python `
    -m compileall `
    .\app\modules\goals `
    .\app\modules\notes `
    .\app\modules\workspace_permissions `
    .\app\modules\tenant_api `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Phase 11.9 compile failed."
}

Write-Host "PASS compile"
Write-Host ""

Write-Host "[2/6] Migration compile..."

& $Python `
    -m py_compile `
    .\migrations\tenant\versions\e4f5a6b7c8d9_add_goals_and_notes.py

if ($LASTEXITCODE -ne 0)
{
    throw "Phase 11.9 migration compile failed."
}

Write-Host "PASS migration compile"
Write-Host ""

Write-Host "[3/6] Application import..."

& $Python `
    -c "from app.main import app; print('PASS app.main import')"

if ($LASTEXITCODE -ne 0)
{
    throw "Application import failed."
}

Write-Host ""

Write-Host "[4/6] Goals + Notes tests..."

& $Python `
    -m pytest `
    .\tests\test_phase11_9_goals_notes_foundation.py `
    .\tests\test_phase11_9_self_identity_contract.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Goals/Notes tests failed."
}

Write-Host "PASS goals + notes tests"
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
    throw "Unable to read tenant Alembic head."
}

Write-Host $Head

# Phase 11.9 now includes:
#
# e4f5a6b7c8d9
#   Goals + Notes
#
# f6a7b8c9d0e1
#   Knowledge
#
# Therefore f6a7b8c9d0e1 is the authoritative
# Phase 11.9 tenant schema head.

if ($Head -notmatch "f6a7b8c9d0e1")
{
    throw "Current Phase 11.9 tenant head f6a7b8c9d0e1 was not found."
}

Write-Host "PASS tenant head"
Write-Host ""

Write-Host "[6/6] OpenAPI contracts..."

$OpenApiCheck = @'
from app.main import app

paths = app.openapi()["paths"]

required = [
    "/api/v1/workspaces/{workspace_id}/goals/me",
    "/api/v1/workspaces/{workspace_id}/goals/me/{goal_id}",
    "/api/v1/workspaces/{workspace_id}/notes/me",
    "/api/v1/workspaces/{workspace_id}/notes/me/{note_id}",
]

for path in required:
    if path not in paths:
        raise SystemExit(
            "Missing route: " + path
        )

print("PASS Phase 11.9 Goals + Notes OpenAPI")
'@

$OpenApiCheck | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Phase 11.9 OpenAPI check failed."
}

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 11.9 GOALS + NOTES FOUNDATION: PASS"
Write-Host " Current schema head: f6a7b8c9d0e1"
Write-Host "================================================="