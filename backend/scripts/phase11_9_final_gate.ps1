param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^tenant_[0-9a-fA-F]{32}$')]
    [string]$DatabaseName
)

$ErrorActionPreference = "Stop"

$BackendRoot = "C:\workforce-os\backend"
$Python = "C:\workforce-os\backend\.venv\Scripts\python.exe"
$TenantAlembicConfig = ".\alembic.tenant.ini"
$ExpectedTenantHead = "f6a7b8c9d0e1"

Set-Location $BackendRoot

Write-Host "================================================="
Write-Host " WorkforceOS Phase 11.9 FINAL Certification"
Write-Host "================================================="
Write-Host ""
Write-Host "Tenant: $DatabaseName"
Write-Host ""

# =========================================================
# 1/8 POSTGRESQL
# =========================================================

Write-Host "[1/8] PostgreSQL..."

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
# 2/8 COMPILE
# =========================================================

Write-Host "[2/8] Compile Phase 11.9..."

& $Python `
    -m compileall `
    .\app\modules\goals `
    .\app\modules\notes `
    .\app\modules\knowledge `
    .\app\modules\ai_productivity `
    .\app\modules\workspace_permissions `
    .\app\modules\tenant_api `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Phase 11.9 compile failed."
}

Write-Host "PASS compile"
Write-Host ""

# =========================================================
# 3/8 PRODUCTIVITY REGRESSION
# =========================================================

Write-Host "[3/8] Productivity regression..."

& ".\scripts\phase11_9_regression_gate.ps1"

if ($LASTEXITCODE -ne 0)
{
    throw "Phase 11.9 regression failed."
}

Write-Host "PASS productivity regression"
Write-Host ""

# =========================================================
# 4/8 AI PRODUCTIVITY TESTS
# =========================================================

Write-Host "[4/8] AI productivity tests..."

& $Python `
    -m pytest `
    .\tests\test_phase11_9_ai_productivity_foundation.py `
    .\tests\test_phase11_9_ai_provider_config.py `
    .\tests\test_phase11_9_ai_privacy_contract.py `
    .\tests\test_phase11_9_ai_security_contract.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "AI productivity tests failed."
}

Write-Host "PASS AI productivity"
Write-Host ""

# =========================================================
# 5/8 OPENAPI CONTRACT
# =========================================================

Write-Host "[5/8] OpenAPI uniqueness..."

& $Python `
    -m pytest `
    .\tests\test_phase11_9_openapi_uniqueness.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "OpenAPI uniqueness test failed."
}

Write-Host "PASS OpenAPI uniqueness"
Write-Host ""

# =========================================================
# 6/8 TENANT SCHEMA
# =========================================================

Write-Host "[6/8] Tenant schema revision..."

$Current = (
    & $Python `
        -m alembic `
        -c $TenantAlembicConfig `
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
    throw "Tenant is not at Phase 11.9 schema head $ExpectedTenantHead."
}

Write-Host "PASS tenant schema"
Write-Host ""

# =========================================================
# 7/8 SAFE DEFAULT AI PROVIDER
# =========================================================

Write-Host "[7/8] Safe default AI provider..."

$ProviderCheck = @'
import os

AI_ENVIRONMENT_VARIABLES = [
    "WORKFORCE_AI_PRODUCTIVITY_ENABLED",
    "WORKFORCE_AI_PRODUCTIVITY_ALLOW_EXTERNAL_PROCESSING",
    "WORKFORCE_AI_PRODUCTIVITY_PROVIDER",
    "WORKFORCE_AI_PRODUCTIVITY_ENDPOINT",
    "WORKFORCE_AI_PRODUCTIVITY_MODEL",
    "WORKFORCE_AI_PRODUCTIVITY_BEARER_TOKEN",
    "WORKFORCE_AI_PRODUCTIVITY_TIMEOUT_SECONDS",
    "WORKFORCE_AI_PRODUCTIVITY_MAX_ITEM_CHARACTERS",
    "WORKFORCE_AI_PRODUCTIVITY_MAX_CONTEXT_CHARACTERS",
]

for name in AI_ENVIRONMENT_VARIABLES:
    os.environ.pop(name, None)

from app.modules.ai_productivity.provider import (
    DisabledAIProductivityProvider,
    get_ai_productivity_provider,
)

provider = get_ai_productivity_provider()

if not isinstance(
    provider,
    DisabledAIProductivityProvider,
):
    raise SystemExit(
        "Default configuration unexpectedly enabled "
        "an external AI provider."
    )

info = provider.info()

if info.external_processing_enabled:
    raise SystemExit(
        "External AI processing is enabled by default."
    )

if info.provider_key != "disabled":
    raise SystemExit(
        "Default provider key must be disabled."
    )

print("PASS safe AI default")
'@

$ProviderCheck | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Safe AI default check failed."
}

Write-Host ""

# =========================================================
# 8/8 APPLICATION + OPENAPI
# =========================================================

Write-Host "[8/8] Application import..."

$ApplicationCheck = @'
from app.main import app

schema = app.openapi()

required_paths = [
    "/api/v1/workspaces/{workspace_id}/goals/me",
    "/api/v1/workspaces/{workspace_id}/notes/me",
    "/api/v1/workspaces/{workspace_id}/knowledge/me",
    "/api/v1/workspaces/{workspace_id}/knowledge/workspace",
    "/api/v1/workspaces/{workspace_id}/ai-productivity/capabilities",
    "/api/v1/workspaces/{workspace_id}/ai-productivity/run",
]

for path in required_paths:
    if path not in schema["paths"]:
        raise SystemExit(
            "Missing Phase 11.9 API route: " + path
        )

print("PASS app + Phase 11.9 OpenAPI")
'@

$ApplicationCheck | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Final application/OpenAPI check failed."
}

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 11.9 FINAL CERTIFICATION: PASS"
Write-Host "================================================="
Write-Host ""
Write-Host "Goals:            PASS"
Write-Host "Notes:            PASS"
Write-Host "Knowledge:        PASS"
Write-Host "Self identity:    PASS"
Write-Host "Permissions:      PASS"
Write-Host "Tenant schema:    $ExpectedTenantHead"
Write-Host "AI orchestration: PASS"
Write-Host "AI privacy:       PASS"
Write-Host "External AI:      OFF by default"
Write-Host "================================================="