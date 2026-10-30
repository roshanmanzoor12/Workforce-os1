$ErrorActionPreference = "Stop"

$BackendRoot = "C:\workforce-os\backend"
$Python = "C:\workforce-os\backend\.venv\Scripts\python.exe"

Set-Location $BackendRoot

Write-Host "================================================="
Write-Host " WorkforceOS Phase 11.8 Monitoring Control Gate"
Write-Host "================================================="
Write-Host ""

Write-Host "[1/5] Compile..."

& $Python `
    -m compileall `
    .\app\modules\monitoring_control `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Monitoring Control compile failed."
}

Write-Host "PASS compile"
Write-Host ""

Write-Host "[2/5] Import contract..."

$ImportScript = @'
from app.modules.monitoring_control.permissions import (
    MONITORING_CONTROL_PERMISSIONS,
)
from app.modules.monitoring_control.service import (
    MonitoringControlService,
)

if not MONITORING_CONTROL_PERMISSIONS:
    raise SystemExit(
        "Monitoring permission registry empty."
    )

print("PASS monitoring permissions import")
print("PASS MonitoringControlService import")
'@

$ImportScript | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Monitoring Control import failed."
}

Write-Host ""

Write-Host "[3/5] Permission policy..."

$PermissionScript = @'
from app.modules.workspace_permissions.permissions import (
    WorkspacePermission,
)
from app.modules.workspace_permissions.policy import (
    WorkspacePermissionPolicy,
)

if not WorkspacePermissionPolicy.allows(
    role_key="admin",
    permission=(
        WorkspacePermission
        .MONITORING_VIEW
        .value
    ),
):
    raise SystemExit(
        "Admin monitoring view missing."
    )

if not WorkspacePermissionPolicy.allows(
    role_key="admin",
    permission=(
        WorkspacePermission
        .MONITORING_LIVE_VIEW
        .value
    ),
):
    raise SystemExit(
        "Admin live monitoring missing."
    )

if WorkspacePermissionPolicy.allows(
    role_key="member",
    permission=(
        WorkspacePermission
        .MONITORING_LIVE_VIEW
        .value
    ),
):
    raise SystemExit(
        "Member must not have "
        "live monitoring permission."
    )

print("PASS admin monitoring view")
print("PASS admin live-screen view")
print("PASS member live-screen denied")
'@

$PermissionScript | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Monitoring permission policy failed."
}

Write-Host ""

Write-Host "[4/5] Privacy boundary..."

$PrivacyScript = @'
from pathlib import Path

root = Path(
    "app/modules/monitoring_control"
)

for path in root.rglob("*.py"):
    text = path.read_text(
        encoding="utf-8",
        errors="ignore",
    ).lower()

    forbidden = [
        "capture_keystrokes",
        "record_keystrokes",
        "capture_clipboard",
        "clipboard_contents",
        "capture_password",
        "password_contents",
        "capture_typed_text",
        "mouse_coordinates =",
        "stealth_mode = true",
    ]

    for token in forbidden:
        if token in text:
            raise SystemExit(
                "Forbidden invasive token "
                + token
                + " in "
                + str(path)
            )

print("PASS no keylogging implementation")
print("PASS no clipboard capture")
print("PASS no password capture")
print("PASS no stealth mode")
'@

$PrivacyScript | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Monitoring privacy boundary failed."
}

Write-Host ""

Write-Host "[5/5] Domain boundary..."

$DomainScript = @'
from pathlib import Path

service = Path(
    "app/modules/monitoring_control/"
    "service.py"
).read_text(
    encoding="utf-8",
)

required = [
    "TenantScope",
    "WorkspacePermissionService",
    "require_monitoring_view",
    "require_monitoring_manage",
    "require_live_screen_view",
    "require_settings_manage",
]

for token in required:
    if token not in service:
        raise SystemExit(
            "Missing monitoring control token: "
            + token
        )

forbidden = [
    "database_url",
    "postgresql://",
    "asyncpg://",
    "tenant_password",
]

lowered = service.lower()

for token in forbidden:
    if token in lowered:
        raise SystemExit(
            "Forbidden tenant routing token: "
            + token
        )

print("PASS trusted TenantScope")
print("PASS centralized workspace permissions")
print("PASS backend tenant boundary")
'@

$DomainScript | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Monitoring domain boundary failed."
}

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 11.8 MONITORING CONTROL PERMISSIONS: PASS"
Write-Host "================================================="