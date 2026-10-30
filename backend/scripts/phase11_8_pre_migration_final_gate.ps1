$ErrorActionPreference = "Stop"

$BackendRoot = "C:\workforce-os\backend"
$Python = "C:\workforce-os\backend\.venv\Scripts\python.exe"

Set-Location $BackendRoot

Write-Host "================================================="
Write-Host " WorkforceOS Phase 11.8 Pre-Migration Final Gate"
Write-Host "================================================="
Write-Host ""

Write-Host "[1/6] Required modules..."

$Required = @(
    ".\app\modules\workspace_permissions",
    ".\app\modules\meetings",
    ".\app\modules\monitoring_control",
    ".\app\modules\tenant_api"
)

foreach ($Path in $Required)
{
    if (
        -not (
            Test-Path $Path
        )
    )
    {
        throw (
            "Missing required path: "
            + $Path
        )
    }

    Write-Host "PASS $Path"
}

Write-Host ""

Write-Host "[2/6] Application import..."

& $Python `
    -c "from app.main import app; print('PASS app.main')"

if (
    $LASTEXITCODE -ne 0
)
{
    throw "Application import failed."
}

Write-Host ""

Write-Host "[3/6] Existing integration gate..."

.\scripts\phase11_8_integration_gate.ps1

if (
    $LASTEXITCODE -ne 0
)
{
    throw "Phase 11.8 integration failed."
}

Write-Host ""

Write-Host "[4/6] Schema metadata..."

.\scripts\phase11_8_schema_metadata_gate.ps1

if (
    $LASTEXITCODE -ne 0
)
{
    throw "Phase 11.8 metadata failed."
}

Write-Host ""

Write-Host "[5/6] Regression suite..."

.\scripts\phase11_8_regression_gate.ps1

if (
    $LASTEXITCODE -ne 0
)
{
    throw "Phase 11.8 regression failed."
}

Write-Host ""

Write-Host "[6/6] OpenAPI health..."

$ApiScript = @'
from app.main import app

schema = app.openapi()

paths = schema.get(
    "paths",
    {},
)

required = [
    (
        "/api/v1/workspaces/"
        "{workspace_id}/permissions/me"
    ),
    (
        "/api/v1/workspaces/"
        "{workspace_id}/meetings"
    ),
    (
        "/api/v1/workspaces/"
        "{workspace_id}/meetings/"
        "{meeting_id}/start"
    ),
    (
        "/api/v1/workspaces/"
        "{workspace_id}/meetings/"
        "{meeting_id}/end"
    ),
    (
        "/api/v1/workspaces/"
        "{workspace_id}/meetings/"
        "me/invitations"
    ),
    (
        "/api/v1/workspaces/"
        "{workspace_id}/"
        "monitoring-control"
    ),
]

for path in required:
    if path not in paths:
        raise SystemExit(
            "Missing API route: "
            + path
        )

print(
    "PASS Phase 11.8 OpenAPI health"
)
'@

$ApiScript | & $Python -

if (
    $LASTEXITCODE -ne 0
)
{
    throw "OpenAPI health failed."
}

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 11.8 PRE-MIGRATION CERTIFICATION: PASS"
Write-Host "================================================="
Write-Host ""
Write-Host (
    "NOTE: Actual tenant Alembic migration "
    + "certification is still required."
)