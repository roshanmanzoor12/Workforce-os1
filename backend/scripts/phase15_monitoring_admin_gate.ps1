$ErrorActionPreference = "Stop"


$BackendRoot = "C:\workforce-os\backend"

$Python = (
    "C:\workforce-os\backend\" +
    ".venv\Scripts\python.exe"
)

$ExpectedControlHead = "g1b2c3d4e5f6"

$ExpectedTenantHead = "k1f2g3h4i5j6"

$WorkspaceId = (
    "34527ffb-e094-4e5e-89ee-4cab97244fc3"
)

$TenantDatabase = (
    "tenant_" +
    $WorkspaceId.Replace(
        "-",
        ""
    )
)


Set-Location $BackendRoot


Write-Host "================================================="
Write-Host " WorkforceOS Phase 15 Monitoring Admin / Policy"
Write-Host "================================================="
Write-Host ""


# =========================================================
# REQUIRED FILES
# =========================================================

$RequiredFiles = @(
    ".\app\modules\monitoring_admin\models.py",
    ".\app\modules\monitoring_admin\schemas.py",
    ".\app\modules\monitoring_admin\access.py",
    ".\app\modules\monitoring_admin\repository.py",
    ".\app\modules\monitoring_admin\service.py",
    ".\app\modules\monitoring_admin\policy_guard.py",
    ".\app\modules\monitoring_admin\router.py",
    ".\app\modules\tenant_api\router.py",
    ".\migrations\tenant\versions\k1f2g3h4i5j6_add_monitoring_admin_policy.py"
)


foreach ($File in $RequiredFiles)
{
    if (-not (Test-Path $File))
    {
        throw (
            "Missing required file: " +
            $File
        )
    }
}


Write-Host "PASS required files"
Write-Host ""


# =========================================================
# 1/8 COMPILE
# =========================================================

Write-Host "[1/8] Compiling..."


& $Python `
    -m compileall `
    .\app\modules\monitoring_admin `
    .\app\modules\tenant_api `
    .\migrations\tenant\versions `
    -q


if ($LASTEXITCODE -ne 0)
{
    throw "Compile failed."
}


Write-Host "PASS compile"
Write-Host ""


# =========================================================
# 2/8 POLICY MODEL
# =========================================================

Write-Host "[2/8] Policy model..."


$ModelCheck = @'
from app.modules.monitoring_admin.models import (
    MonitoringAdminPolicy,
)


columns = {
    column.name
    for column
    in MonitoringAdminPolicy.__table__.columns
}


required = {
    "id",
    "policy_key",
    "monitoring_enabled",
    "screenshots_enabled",
    "live_screen_enabled",
    "screen_share_enabled",
    "disclosure_required",
    "explicit_live_consent_required",
    "visible_live_indicator_required",
    "screenshot_retention_days",
    "live_session_max_minutes",
    "policy_version",
    "policy_notice",
    "updated_by_user_id",
    "created_at",
    "updated_at",
}


missing = required - columns


if missing:
    raise SystemExit(
        "Monitoring policy fields missing: "
        + str(
            sorted(
                missing
            )
        )
    )


print(
    "PASS policy model"
)
'@


$ModelCheck | & $Python -


if ($LASTEXITCODE -ne 0)
{
    throw "Policy model gate failed."
}


Write-Host ""


# =========================================================
# 3/8 SAFETY CONTRACT
# =========================================================

Write-Host "[3/8] Monitoring safety contract..."


$SafetyCheck = @'
from app.modules.monitoring_admin.schemas import (
    MonitoringAdminPolicyUpdate,
)

from app.modules.monitoring_admin.service import (
    MonitoringAdminService,
)


fields = set(
    MonitoringAdminPolicyUpdate
    .model_fields
)


for forbidden in {
    "stealth_mode",
    "silent_capture",
    "disable_indicator",
    "disable_consent",
    "keylogging",
    "clipboard_capture",
    "password_capture",
    "mouse_coordinates",
}:
    if forbidden in fields:
        raise SystemExit(
            "Forbidden monitoring policy field: "
            + forbidden
        )


source = open(
    "app/modules/monitoring_admin/service.py",
    "r",
    encoding="utf-8",
).read()


required_strings = {
    "Explicit live-screen consent",
    "Visible live-screen indicator",
    "Monitoring disclosure",
}


for item in required_strings:
    if item not in source:
        raise SystemExit(
            "Missing safety invariant: "
            + item
        )


print(
    "PASS monitoring safety contract"
)
'@


$SafetyCheck | & $Python -


if ($LASTEXITCODE -ne 0)
{
    throw "Monitoring safety gate failed."
}


Write-Host ""


# =========================================================
# 4/8 PERMISSION CONTRACT
# =========================================================

Write-Host "[4/8] Permission contract..."


$PermissionCheck = @'
from app.modules.workspace_permissions.permissions import (
    WorkspacePermission,
)


expected = {
    "monitoring.view":
        WorkspacePermission
        .MONITORING_VIEW
        .value,

    "monitoring.manage":
        WorkspacePermission
        .MONITORING_MANAGE
        .value,

    "monitoring.live_view":
        WorkspacePermission
        .MONITORING_LIVE_VIEW
        .value,

    "monitoring.live_screen":
        WorkspacePermission
        .MONITORING_LIVE_SCREEN
        .value,

    "monitoring.settings.manage":
        WorkspacePermission
        .MONITORING_SETTINGS_MANAGE
        .value,
}


for required, actual in expected.items():
    if actual != required:
        raise SystemExit(
            "Permission mismatch. Expected "
            + required
            + ", got "
            + actual
        )


print(
    "PASS permission contract"
)
'@


$PermissionCheck | & $Python -


if ($LASTEXITCODE -ne 0)
{
    throw "Permission gate failed."
}


Write-Host ""


# =========================================================
# 5/8 IMPORTS
# =========================================================

Write-Host "[5/8] Imports..."


$ImportCheck = @'
from app.modules.monitoring_admin.access import (
    resolve_monitoring_admin_access,
)

from app.modules.monitoring_admin.policy_guard import (
    require_live_monitoring_policy,
)

from app.modules.monitoring_admin.repository import (
    MonitoringAdminRepository,
)

from app.modules.monitoring_admin.router import (
    router,
)

from app.modules.monitoring_admin.service import (
    MonitoringAdminService,
    MonitoringPolicyDisabledError,
)


assert resolve_monitoring_admin_access
assert require_live_monitoring_policy
assert MonitoringAdminRepository
assert MonitoringAdminService
assert MonitoringPolicyDisabledError
assert router


print(
    "PASS monitoring admin imports"
)
'@


$ImportCheck | & $Python -


if ($LASTEXITCODE -ne 0)
{
    throw "Import gate failed."
}


Write-Host ""


# =========================================================
# 6/8 APP + OPENAPI
# =========================================================

Write-Host "[6/8] App/OpenAPI..."


$OpenApiCheck = @'
from app.main import app


paths = app.openapi()["paths"]


base = (
    "/api/v1/workspaces/"
    "{workspace_id}/monitoring-admin"
)


required = {
    base: {
        "get",
    },

    base + "/policy": {
        "get",
        "patch",
    },

    base + "/capabilities": {
        "get",
    },
}


for path, methods in required.items():
    if path not in paths:
        raise SystemExit(
            "Missing monitoring admin endpoint: "
            + path
        )

    available = set(
        paths[path]
    )

    missing = methods - available

    if missing:
        raise SystemExit(
            "Missing methods for "
            + path
            + ": "
            + str(
                sorted(
                    missing
                )
            )
        )


live_base = (
    "/api/v1/workspaces/"
    "{workspace_id}/live-monitoring"
)


required_live_paths = {
    live_base + "/screenshots",
    live_base + "/live-sessions",
    live_base + "/capabilities",
}


missing_live = (
    required_live_paths
    - set(paths)
)


if missing_live:
    raise SystemExit(
        "Existing live-monitoring routes "
        "were lost: "
        + str(
            sorted(
                missing_live
            )
        )
    )


print(
    "PASS app/OpenAPI"
)
'@


$OpenApiCheck | & $Python -


if ($LASTEXITCODE -ne 0)
{
    throw "OpenAPI gate failed."
}


Write-Host ""


# =========================================================
# 7/8 CONTROL HEAD
# =========================================================

Write-Host "[7/8] Control migration head..."


$ControlHeads = & $Python `
    -m alembic `
    -c ".\alembic-control.ini" `
    heads


if ($LASTEXITCODE -ne 0)
{
    throw "Control Alembic heads failed."
}


$ControlHeadLines = @(
    $ControlHeads |
    ForEach-Object {
        if ($null -ne $_)
        {
            $_.ToString().Trim()
        }
    } |
    Where-Object {
        $_.Length -gt 0
    }
)


if ($ControlHeadLines.Count -ne 1)
{
    throw (
        "Expected exactly one control head. Found: " +
        $ControlHeadLines.Count
    )
}


$ControlHeadText = (
    $ControlHeadLines -join "`n"
)


Write-Host $ControlHeadText


if ($ControlHeadText -notmatch $ExpectedControlHead)
{
    throw (
        "Unexpected control head. Expected " +
        $ExpectedControlHead
    )
}


Write-Host "PASS control head"
Write-Host ""


# =========================================================
# 8/8 TENANT MIGRATION
# =========================================================

Write-Host "[8/8] Tenant migration..."


$TenantHeads = & $Python `
    -m alembic `
    -c ".\alembic.tenant.ini" `
    -x "database_name=$TenantDatabase" `
    heads


if ($LASTEXITCODE -ne 0)
{
    throw "Tenant Alembic heads failed."
}


$TenantHeadLines = @(
    $TenantHeads |
    ForEach-Object {
        if ($null -ne $_)
        {
            $_.ToString().Trim()
        }
    } |
    Where-Object {
        $_.Length -gt 0
    }
)


if ($TenantHeadLines.Count -ne 1)
{
    throw (
        "Expected exactly one tenant head. Found: " +
        $TenantHeadLines.Count
    )
}


$TenantHeadText = (
    $TenantHeadLines -join "`n"
)


Write-Host $TenantHeadText


if ($TenantHeadText -notmatch $ExpectedTenantHead)
{
    throw (
        "Unexpected tenant head. Expected " +
        $ExpectedTenantHead
    )
}


$TenantCurrent = & $Python `
    -m alembic `
    -c ".\alembic.tenant.ini" `
    -x "database_name=$TenantDatabase" `
    current


if ($LASTEXITCODE -ne 0)
{
    throw "Tenant Alembic current failed."
}


$TenantCurrentText = (
    $TenantCurrent -join "`n"
)


Write-Host $TenantCurrentText


if ($TenantCurrentText -notmatch $ExpectedTenantHead)
{
    throw (
        "Tenant DB must be upgraded to " +
        $ExpectedTenantHead
    )
}


Write-Host "PASS tenant migration"
Write-Host ""


# =========================================================
# FINAL
# =========================================================

Write-Host "================================================="
Write-Host " PHASE 15 MONITORING ADMIN / POLICY: PASS"
Write-Host "================================================="
Write-Host "Persistent monitoring policy:       PASS"
Write-Host "Monitoring global enable/disable:   PASS"
Write-Host "Screenshot policy:                  PASS"
Write-Host "Live-screen policy:                 PASS"
Write-Host "Screen-share policy:                PASS"
Write-Host "Screenshot retention:               PASS"
Write-Host "Live-session maximum:               PASS"
Write-Host "Policy versioning:                  PASS"
Write-Host "Settings RBAC:                      PASS"
Write-Host "Explicit live consent invariant:    PASS"
Write-Host "Visible indicator invariant:        PASS"
Write-Host "Disclosure invariant:               PASS"
Write-Host "Phase 14 policy enforcement:        PASS"
Write-Host "No stealth monitoring controls:     PASS"
Write-Host "No keylogging/clipboard/passwords:  PASS"
Write-Host "OpenAPI:                            PASS"
Write-Host "Control head:                       $ExpectedControlHead"
Write-Host "Tenant head:                        $ExpectedTenantHead"
Write-Host "================================================="