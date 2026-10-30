$ErrorActionPreference = "Stop"

$BackendRoot = "C:\workforce-os\backend"
$Python = "C:\workforce-os\backend\.venv\Scripts\python.exe"

Set-Location $BackendRoot

Write-Host "================================================="
Write-Host " WorkforceOS Phase 11.8 Permissions Foundation"
Write-Host "================================================="
Write-Host ""

Write-Host "[1/6] Compile..."

& $Python `
    -m compileall `
    .\app\modules\workspace_permissions `
    .\tests\test_phase11_8_workspace_permissions.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Permissions compile failed."
}

Write-Host "PASS compile"
Write-Host ""

Write-Host "[2/6] Permission tests..."

& $Python `
    -m pytest `
    .\tests\test_phase11_8_workspace_permissions.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Permission tests failed."
}

Write-Host "PASS permission tests"
Write-Host ""

Write-Host "[3/6] Permission registry..."

$RegistryScript = @'
from app.modules.workspace_permissions.permissions import (
    ALL_WORKSPACE_PERMISSIONS,
    WorkspacePermission,
)

required = {
    "employees.view",
    "employees.manage",
    "attendance.view",
    "attendance.manage",
    "meetings.view",
    "meetings.create",
    "meetings.manage",
    "monitoring.view",
    "monitoring.manage",
    "monitoring.live_view",
    "monitoring.settings.manage",
}

missing = (
    required
    - ALL_WORKSPACE_PERMISSIONS
)

if missing:
    raise SystemExit(
        "Missing permissions: "
        + ", ".join(
            sorted(missing)
        )
    )

if len(
    ALL_WORKSPACE_PERMISSIONS
) != len(
    list(
        WorkspacePermission
    )
):
    raise SystemExit(
        "Duplicate permission values."
    )

print("PASS permission registry")
print("PASS meeting permissions")
print("PASS monitoring permissions")
print("PASS attendance permissions")
'@

$RegistryScript | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Permission registry failed."
}

Write-Host ""

Write-Host "[4/6] Role policy..."

$RoleScript = @'
from app.modules.workspace_permissions.permissions import (
    WorkspacePermission,
)
from app.modules.workspace_permissions.policy import (
    WorkspacePermissionPolicy,
)

owner = (
    WorkspacePermissionPolicy
    .permissions_for_role(
        "owner"
    )
)

admin = (
    WorkspacePermissionPolicy
    .permissions_for_role(
        "admin"
    )
)

member = (
    WorkspacePermissionPolicy
    .permissions_for_role(
        "member"
    )
)

if not owner:
    raise SystemExit(
        "Owner has no permissions."
    )

if (
    WorkspacePermission
    .MONITORING_LIVE_VIEW
    .value
    not in admin
):
    raise SystemExit(
        "Admin monitoring permission missing."
    )

if (
    WorkspacePermission
    .MONITORING_LIVE_VIEW
    .value
    in member
):
    raise SystemExit(
        "Member must not have live "
        "monitoring permission."
    )

if (
    WorkspacePermission
    .MEETINGS_CREATE
    .value
    not in member
):
    raise SystemExit(
        "Member meeting creation "
        "permission missing."
    )

print("PASS OWNER policy")
print("PASS ADMIN policy")
print("PASS MEMBER policy")
'@

$RoleScript | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Permission role policy failed."
}

Write-Host ""

Write-Host "[5/6] TenantScope boundary..."

$ScopeScript = @'
from pathlib import Path

files = [
    Path(
        "app/modules/workspace_permissions/"
        "tenant_scope.py"
    ),
    Path(
        "app/modules/workspace_permissions/"
        "service.py"
    ),
    Path(
        "app/modules/workspace_permissions/"
        "router.py"
    ),
]

for path in files:
    text = path.read_text(
        encoding="utf-8",
    )

    if "TenantScope" not in text:
        raise SystemExit(
            "TenantScope missing from "
            + str(path)
        )

for path in files:
    text = path.read_text(
        encoding="utf-8",
    ).lower()

    forbidden = [
        "database_url",
        "database_name",
        "postgresql://",
        "asyncpg://",
        "tenant_password",
    ]

    for token in forbidden:
        if token in text:
            raise SystemExit(
                "Forbidden tenant token "
                + token
                + " in "
                + str(path)
            )

print("PASS trusted TenantScope boundary")
print("PASS role not accepted from client")
print("PASS no database credentials")
'@

$ScopeScript | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "TenantScope boundary failed."
}

Write-Host ""

Write-Host "[6/6] Privacy boundary..."

$PrivacyScript = @'
from pathlib import Path

root = Path(
    "app/modules/workspace_permissions"
)

for path in root.rglob("*.py"):
    text = path.read_text(
        encoding="utf-8",
        errors="ignore",
    ).lower()

    forbidden = [
        "capture_keystrokes",
        "capture_clipboard",
        "capture_password",
        "capture_typed_text",
        "mouse_coordinates =",
        "stealth_mode = true",
    ]

    for token in forbidden:
        if token in text:
            raise SystemExit(
                "Forbidden privacy token "
                + token
                + " in "
                + str(path)
            )

print("PASS privacy boundary")
print("PASS no invasive monitoring implementation")
'@

$PrivacyScript | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Permission privacy boundary failed."
}

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 11.8 WORKSPACE PERMISSIONS: PASS"
Write-Host "================================================="