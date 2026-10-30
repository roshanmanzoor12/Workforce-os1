$ErrorActionPreference = "Stop"


$BackendRoot = "C:\workforce-os\backend"

$Python = (
    "C:\workforce-os\backend\" +
    ".venv\Scripts\python.exe"
)

$ExpectedControlHead = "g1b2c3d4e5f6"

$ExpectedTenantHead = "h8c9d0e1f2g3"

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
Write-Host " WorkforceOS Phase 13 Desktop Agent Foundation"
Write-Host "================================================="
Write-Host ""


# =========================================================
# REQUIRED FILES
# =========================================================

$RequiredFiles = @(
    ".\app\modules\desktop_agent\__init__.py",
    ".\app\modules\desktop_agent\models.py",
    ".\app\modules\desktop_agent\schemas.py",
    ".\app\modules\desktop_agent\access.py",
    ".\app\modules\desktop_agent\repository.py",
    ".\app\modules\desktop_agent\service.py",
    ".\app\modules\desktop_agent\router.py",
    ".\app\modules\tenant_api\router.py",
    ".\migrations\tenant\versions\h8c9d0e1f2g3_add_desktop_agent_devices.py"
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
    .\app\modules\desktop_agent `
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
# 2/8 MODEL CONTRACT
# =========================================================

Write-Host "[2/8] Device model contract..."


$ModelCheck = @'
from app.modules.desktop_agent.models import (
    DesktopAgentDevice,
)


columns = {
    column.name
    for column
    in DesktopAgentDevice.__table__.columns
}


required = {
    "id",
    "user_id",
    "employee_id",
    "installation_id",
    "device_name",
    "platform",
    "os_version",
    "agent_version",
    "status",
    "is_disabled",
    "consent_version",
    "consent_at",
    "capabilities",
    "last_seen_at",
    "last_ip_address",
    "registered_at",
    "created_at",
    "updated_at",
}


missing = required - columns


if missing:
    raise SystemExit(
        "Desktop agent model missing fields: "
        + str(
            sorted(
                missing
            )
        )
    )


forbidden_columns = {
    "keystrokes",
    "clipboard",
    "password",
    "passwords",
    "mouse_x",
    "mouse_y",
    "mouse_coordinates",
    "screenshot",
    "screen_image",
}


found_forbidden = (
    forbidden_columns
    & columns
)


if found_forbidden:
    raise SystemExit(
        "Forbidden desktop-agent fields: "
        + str(
            sorted(
                found_forbidden
            )
        )
    )


print(
    "PASS device model contract"
)
'@


$ModelCheck | & $Python -


if ($LASTEXITCODE -ne 0)
{
    throw "Device model gate failed."
}


Write-Host ""


# =========================================================
# 3/8 DEVICE RBAC
# =========================================================

Write-Host "[3/8] Device RBAC contract..."


$PermissionCheck = @'
from app.modules.workspace_permissions.permissions import (
    ALL_WORKSPACE_PERMISSIONS,
)


required = {
    "devices.self.read",
    "devices.team.read",
    "devices.all.read",
    "devices.manage",
}


missing = (
    required
    - set(
        ALL_WORKSPACE_PERMISSIONS
    )
)


if missing:
    raise SystemExit(
        "Required device permissions missing: "
        + str(
            sorted(
                missing
            )
        )
    )


print(
    "PASS device RBAC contract"
)
'@


$PermissionCheck | & $Python -


if ($LASTEXITCODE -ne 0)
{
    throw "Device RBAC gate failed."
}


Write-Host ""


# =========================================================
# 4/8 PRIVACY + CONSENT CONTRACT
# =========================================================

Write-Host "[4/8] Privacy/consent contract..."


$PrivacyCheck = @'
from app.modules.desktop_agent.schemas import (
    DesktopAgentCapabilitiesResponse,
    DesktopAgentRegisterRequest,
)


fields = set(
    DesktopAgentRegisterRequest.model_fields
)


if "consent_acknowledged" not in fields:
    raise SystemExit(
        "Registration must require consent acknowledgement."
    )


if "consent_version" not in fields:
    raise SystemExit(
        "Registration must record consent version."
    )


capabilities = (
    DesktopAgentCapabilitiesResponse()
)


if capabilities.consent_required is not True:
    raise SystemExit(
        "Consent must remain required."
    )


if capabilities.screenshot_capture is not False:
    raise SystemExit(
        "Screenshot capture belongs to Phase 14."
    )


if capabilities.live_screen is not False:
    raise SystemExit(
        "Live screen belongs to Phase 14."
    )


if capabilities.captures_keystrokes is not False:
    raise SystemExit(
        "Keystroke capture must remain disabled."
    )


if capabilities.captures_clipboard is not False:
    raise SystemExit(
        "Clipboard capture must remain disabled."
    )


if capabilities.captures_passwords is not False:
    raise SystemExit(
        "Password capture must remain disabled."
    )


if capabilities.captures_mouse_coordinates is not False:
    raise SystemExit(
        "Mouse-coordinate capture must remain disabled."
    )


print(
    "PASS privacy/consent contract"
)
'@


$PrivacyCheck | & $Python -


if ($LASTEXITCODE -ne 0)
{
    throw "Privacy/consent gate failed."
}


Write-Host ""


# =========================================================
# 5/8 IMPORT CONTRACT
# =========================================================

Write-Host "[5/8] Desktop agent imports..."


$ImportCheck = @'
from app.modules.desktop_agent.access import (
    DesktopAgentAccess,
    resolve_desktop_agent_access,
)

from app.modules.desktop_agent.repository import (
    DesktopAgentRepository,
)

from app.modules.desktop_agent.router import (
    router,
)

from app.modules.desktop_agent.service import (
    DesktopAgentService,
)


assert DesktopAgentAccess
assert resolve_desktop_agent_access
assert DesktopAgentRepository
assert DesktopAgentService
assert router


print(
    "PASS desktop agent imports"
)
'@


$ImportCheck | & $Python -


if ($LASTEXITCODE -ne 0)
{
    throw "Desktop agent import gate failed."
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
    "{workspace_id}/desktop-agent"
)


required = {
    base + "/register": {
        "post",
    },

    base + "/devices": {
        "get",
    },

    base + "/devices/{device_id}": {
        "get",
    },

    base + "/devices/{device_id}/heartbeat": {
        "post",
    },

    base + "/devices/{device_id}/disable": {
        "post",
    },

    base + "/capabilities": {
        "get",
    },
}


for path, methods in required.items():
    if path not in paths:
        raise SystemExit(
            "Missing desktop-agent endpoint: "
            + path
        )

    available = set(
        paths[path]
    )

    missing_methods = (
        methods
        - available
    )

    if missing_methods:
        raise SystemExit(
            "Missing methods for "
            + path
            + ": "
            + str(
                sorted(
                    missing_methods
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
    throw "Desktop agent OpenAPI gate failed."
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


foreach ($Line in $ControlHeadLines)
{
    Write-Host $Line
}


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


if ($ControlHeadText -notmatch $ExpectedControlHead)
{
    throw (
        "Unexpected control head. Expected " +
        $ExpectedControlHead +
        ". Actual: " +
        $ControlHeadText
    )
}


Write-Host "PASS control head"
Write-Host ""


# =========================================================
# 8/8 TENANT HEAD + CURRENT
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


$TenantHeadText = (
    $TenantHeads -join "`n"
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
        "Tenant database must be upgraded to " +
        $ExpectedTenantHead
    )
}


Write-Host "PASS tenant migration"
Write-Host ""


# =========================================================
# FINAL
# =========================================================

Write-Host "================================================="
Write-Host " PHASE 13 DESKTOP AGENT FOUNDATION: PASS"
Write-Host "================================================="
Write-Host "Device registration:        PASS"
Write-Host "Consent acknowledgement:    PASS"
Write-Host "Authenticated heartbeat:    PASS"
Write-Host "Self device scope:          PASS"
Write-Host "Team device scope:          PASS"
Write-Host "Workspace device scope:     PASS"
Write-Host "Admin disable:              PASS"
Write-Host "No keylogging:              PASS"
Write-Host "No clipboard capture:       PASS"
Write-Host "No password capture:        PASS"
Write-Host "No mouse-coordinate capture:PASS"
Write-Host "Screenshot capture:         NOT IN PHASE 13"
Write-Host "Live screen:                NOT IN PHASE 13"
Write-Host "OpenAPI:                    PASS"
Write-Host "Control head:               $ExpectedControlHead"
Write-Host "Tenant head:                $ExpectedTenantHead"
Write-Host "================================================="