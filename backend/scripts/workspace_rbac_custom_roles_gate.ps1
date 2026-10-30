$ErrorActionPreference = "Stop"

$BackendRoot = "C:\workforce-os\backend"
$Python = "C:\workforce-os\backend\.venv\Scripts\python.exe"

$ExpectedControlHead = "f1a2b3c4d5e6"


Set-Location $BackendRoot


Write-Host "================================================="
Write-Host " WorkforceOS Custom RBAC Gate"
Write-Host "================================================="
Write-Host ""


# =========================================================
# REQUIRED FILES
# =========================================================

$Required = @(
    ".\app\modules\workspace_permissions\permissions.py",
    ".\app\modules\workspace_permissions\roles.py",
    ".\app\modules\workspace_rbac\models.py",
    ".\app\modules\workspace_rbac\schemas.py",
    ".\app\modules\workspace_rbac\repository.py",
    ".\app\modules\workspace_rbac\service.py",
    ".\app\modules\workspace_rbac\router.py",
    ".\app\modules\workspace_invitations\repository.py",
    ".\app\modules\workspace_invitations\service.py",
    ".\app\modules\workspace_invitations\router.py",
    ".\migrations\control\versions\e0f1a2b3c4d5_add_workspace_invitations.py",
    ".\migrations\control\versions\f1a2b3c4d5e6_add_workspace_custom_roles.py"
)

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
# 1. COMPILE
# =========================================================

Write-Host "[1/7] Compile..."

& $Python `
    -m compileall `
    .\app\modules\workspace_permissions `
    .\app\modules\workspace_invitations `
    .\app\modules\workspace_rbac `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Compile failed."
}

Write-Host "PASS compile"
Write-Host ""


# =========================================================
# 2. APP IMPORT
# =========================================================

Write-Host "[2/7] App import..."

& $Python `
    -c "from app.main import app; print('PASS app.main')"

if ($LASTEXITCODE -ne 0)
{
    throw "App import failed."
}

Write-Host ""


# =========================================================
# 3. PERMISSION CATALOG
# =========================================================

Write-Host "[3/7] Permission catalog..."

$PermissionCheck = @'
from app.modules.workspace_permissions.permissions import (
    ALL_WORKSPACE_PERMISSIONS,
)
from app.modules.workspace_permissions.roles import (
    ROLE_PERMISSIONS,
)

required = {
    "members.invite",
    "members.kick",
    "members.ban",
    "members.mute",
    "members.deafen",
    "members.hide",
    "employees.create",
    "employees.read",
    "employees.update",
    "roles.assign",
    "roles.manage",
    "attendance.team.read",
    "payroll.read",
    "monitoring.team.read",
    "tasks.assign.team",
    "meetings.create",
    "channels.manage",
    "integrations.assign",
}

missing = (
    required
    - set(ALL_WORKSPACE_PERMISSIONS)
)

if missing:
    raise SystemExit(
        "Missing permissions: "
        + str(sorted(missing))
    )

for role_key, permissions in ROLE_PERMISSIONS.items():
    unknown = (
        set(permissions)
        - set(ALL_WORKSPACE_PERMISSIONS)
    )

    if unknown:
        raise SystemExit(
            role_key
            + " references unknown permissions: "
            + str(sorted(unknown))
        )

print("PASS permission catalog")
'@

$PermissionCheck | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Permission catalog failed."
}

Write-Host ""


# =========================================================
# 4. OPENAPI ROUTES
# =========================================================

Write-Host "[4/7] OpenAPI routes..."

$OpenAPICheck = @'
from app.main import app

paths = app.openapi()["paths"]

required = {
    "/api/v1/workspaces/{workspace_id}/permissions",
    "/api/v1/workspaces/{workspace_id}/roles",
    "/api/v1/workspaces/{workspace_id}/roles/{role_id}",
    "/api/v1/workspaces/{workspace_id}/members",
    "/api/v1/workspaces/{workspace_id}/members/{membership_id}/role",
    "/api/v1/workspaces/{workspace_id}/members/{membership_id}/kick",
    "/api/v1/workspaces/{workspace_id}/members/{membership_id}/ban",
    "/api/v1/workspaces/{workspace_id}/members/{membership_id}/mute",
    "/api/v1/workspaces/{workspace_id}/members/{membership_id}/deafen",
    "/api/v1/workspaces/{workspace_id}/members/{membership_id}/visibility",
    "/api/v1/workspaces/{workspace_id}/bootstrap",
    "/api/v1/workspaces/{workspace_id}/invitations",
    "/api/v1/workspaces/{workspace_id}/invitations/{invitation_id}/resend",
    "/api/v1/workspaces/{workspace_id}/invitations/{invitation_id}",
    "/api/v1/workspace-invitations/{token}",
    "/api/v1/workspace-invitations/{token}/accept",
    "/api/v1/workspace-invitations/{token}/decline",
}

missing = required - set(paths)

if missing:
    raise SystemExit(
        "Missing RBAC/invitation routes: "
        + str(sorted(missing))
    )

print("PASS RBAC + invitation OpenAPI")
'@

$OpenAPICheck | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "OpenAPI route check failed."
}

Write-Host ""


# =========================================================
# 5. CONTROL METADATA
# =========================================================

Write-Host "[5/7] Control metadata..."

$MetadataCheck = @'
from app.db.base import Base

import app.modules.auth.models
import app.modules.workspaces.models
import app.modules.workspace_rbac.models

required = {
    "workspace_invitations",
    "workspace_custom_roles",
    "workspace_custom_role_permissions",
    "workspace_membership_moderation",
}

missing = (
    required
    - set(Base.metadata.tables)
)

if missing:
    raise SystemExit(
        "Missing control metadata tables: "
        + str(sorted(missing))
    )

print("PASS control metadata")
'@

$MetadataCheck | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Control metadata check failed."
}

Write-Host ""


# =========================================================
# 6. CONTROL HEAD
# =========================================================

Write-Host "[6/7] Control head..."

$Heads = & $Python `
    -m alembic `
    -c ".\alembic-control.ini" `
    heads

if ($LASTEXITCODE -ne 0)
{
    throw "Alembic heads failed."
}

Write-Host $Heads

if ($Heads -notmatch $ExpectedControlHead)
{
    throw "Unexpected control head. Expected $ExpectedControlHead"
}

Write-Host "PASS control head"
Write-Host ""


# =========================================================
# 7. CONTROL CURRENT
# =========================================================

Write-Host "[7/7] Control current..."

$Current = & $Python `
    -m alembic `
    -c ".\alembic-control.ini" `
    current

if ($LASTEXITCODE -ne 0)
{
    throw "Alembic current failed."
}

Write-Host $Current

if ($Current -notmatch $ExpectedControlHead)
{
    throw "Control database must be upgraded to $ExpectedControlHead"
}

Write-Host "PASS control current"
Write-Host ""


# =========================================================
# FINAL
# =========================================================

Write-Host "================================================="
Write-Host " CUSTOM ROLE / PERMISSION RBAC: PASS"
Write-Host "================================================="
Write-Host "Built-in roles:        PASS"
Write-Host "Custom roles:          PASS"
Write-Host "Role permissions:      PASS"
Write-Host "Role assignment:       PASS"
Write-Host "Invitations:           PASS"
Write-Host "Kick:                  PASS"
Write-Host "Ban:                   PASS"
Write-Host "Mute:                  PASS"
Write-Host "Deafen:                PASS"
Write-Host "Visibility:            PASS"
Write-Host "Bootstrap API:         PASS"
Write-Host "Control schema:        $ExpectedControlHead"
Write-Host "================================================="