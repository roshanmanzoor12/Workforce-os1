$ErrorActionPreference = "Stop"

$BackendRoot = "C:\workforce-os\backend"
$Python = "C:\workforce-os\backend\.venv\Scripts\python.exe"

Set-Location $BackendRoot

Write-Host "================================================="
Write-Host " WorkforceOS Phase 11.9 Regression Gate"
Write-Host "================================================="
Write-Host ""

Write-Host "[1/5] Compile..."

& $Python `
    -m compileall `
    .\app\modules\goals `
    .\app\modules\notes `
    .\app\modules\knowledge `
    .\app\modules\workspace_permissions `
    .\app\modules\tenant_api `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Phase 11.9 compile failed."
}

Write-Host "PASS compile"
Write-Host ""

Write-Host "[2/5] Goals + Notes..."

& $Python `
    -m pytest `
    .\tests\test_phase11_9_goals_notes_foundation.py `
    .\tests\test_phase11_9_self_identity_contract.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Goals/Notes regression failed."
}

Write-Host "PASS goals + notes"
Write-Host ""

Write-Host "[3/5] Knowledge..."

& $Python `
    -m pytest `
    .\tests\test_phase11_9_knowledge_foundation.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Knowledge regression failed."
}

Write-Host "PASS knowledge"
Write-Host ""

Write-Host "[4/5] Migration contracts..."

& $Python `
    -m pytest `
    .\tests\test_phase11_9_goals_notes_migration_contract.py `
    .\tests\test_phase11_9_knowledge_migration_contract.py `
    .\tests\test_phase11_9_model_migration_parity.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Migration regression failed."
}

Write-Host "PASS migrations"
Write-Host ""

Write-Host "[5/5] Application + OpenAPI..."

$Check = @'
from app.main import app

paths = app.openapi()["paths"]

required = [
    "/api/v1/workspaces/{workspace_id}/goals/me",
    "/api/v1/workspaces/{workspace_id}/notes/me",
    "/api/v1/workspaces/{workspace_id}/knowledge/me",
    "/api/v1/workspaces/{workspace_id}/knowledge/workspace",
]

for path in required:
    if path not in paths:
        raise SystemExit(
            "Missing API route: "
            + path
        )

print("PASS app + OpenAPI")
'@

$Check | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Application/OpenAPI regression failed."
}

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 11.9 REGRESSION: PASS"
Write-Host "================================================="