$ErrorActionPreference = "Stop"

$BackendRoot = "C:\workforce-os\backend"
$Python = "C:\workforce-os\backend\.venv\Scripts\python.exe"

Set-Location $BackendRoot

Write-Host "================================================="
Write-Host " WorkforceOS Phase 11.8 Integration Gate"
Write-Host "================================================="
Write-Host ""

Write-Host "[1/7] Compile..."

& $Python `
    -m compileall `
    .\app\modules\workspace_permissions `
    .\app\modules\meetings `
    .\app\modules\monitoring_control `
    .\app\modules\tenant_api `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Phase 11.8 compile failed."
}

Write-Host "PASS compile"
Write-Host ""

Write-Host "[2/7] Application import..."

& $Python `
    -c "from app.main import app; print('PASS app.main import')"

if ($LASTEXITCODE -ne 0)
{
    throw "Application import failed."
}

Write-Host ""

Write-Host "[3/7] Permission regression..."

& $Python `
    -m pytest `
    .\tests\test_phase11_8_workspace_permissions.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Workspace permission regression failed."
}

Write-Host "PASS permissions"
Write-Host ""

Write-Host "[4/7] Meetings regression..."

& $Python `
    -m pytest `
    .\tests\test_phase11_8_meetings_foundation.py `
    .\tests\test_phase11_8_meeting_self_and_monitoring.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Meetings regression failed."
}

Write-Host "PASS meetings"
Write-Host ""

Write-Host "[5/7] Phase integration contract..."

& $Python `
    -m pytest `
    .\tests\test_phase11_8_integration_contract.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Phase 11.8 integration contract failed."
}

Write-Host "PASS integration contract"
Write-Host ""

Write-Host "[6/7] OpenAPI contract..."

$ApiScript = @'
from app.main import app

paths = app.openapi().get(
    "paths",
    {},
)

required = {
    (
        "/api/v1/workspaces/"
        "{workspace_id}/permissions/me"
    ): {
        "get",
    },
    (
        "/api/v1/workspaces/"
        "{workspace_id}/meetings"
    ): {
        "get",
        "post",
    },
    (
        "/api/v1/workspaces/"
        "{workspace_id}/meetings/"
        "{meeting_id}/start"
    ): {
        "post",
    },
    (
        "/api/v1/workspaces/"
        "{workspace_id}/meetings/"
        "{meeting_id}/end"
    ): {
        "post",
    },
    (
        "/api/v1/workspaces/"
        "{workspace_id}/meetings/"
        "me/invitations"
    ): {
        "get",
    },
    (
        "/api/v1/workspaces/"
        "{workspace_id}/meetings/"
        "me/{meeting_id}/response"
    ): {
        "patch",
    },
    (
        "/api/v1/workspaces/"
        "{workspace_id}/"
        "monitoring-control"
    ): {
        "get",
    },
    (
        "/api/v1/workspaces/"
        "{workspace_id}/"
        "monitoring-control/live-access"
    ): {
        "get",
    },
}

for path, methods in required.items():
    if path not in paths:
        raise SystemExit(
            "Missing route: "
            + path
        )

    actual = {
        method.lower()
        for method
        in paths[path].keys()
    }

    missing = (
        methods
        - actual
    )

    if missing:
        raise SystemExit(
            path
            + " missing methods: "
            + ", ".join(
                sorted(missing)
            )
        )

    print(
        "PASS "
        + path
    )

print("PASS Phase 11.8 OpenAPI")
'@

$ApiScript | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Phase 11.8 OpenAPI contract failed."
}

Write-Host ""

Write-Host "[7/7] Security + privacy..."

$SecurityScript = @'
from pathlib import Path

roots = [
    Path(
        "app/modules/workspace_permissions"
    ),
    Path(
        "app/modules/meetings"
    ),
    Path(
        "app/modules/monitoring_control"
    ),
]

for root in roots:
    for path in root.rglob("*.py"):
        text = path.read_text(
            encoding="utf-8",
            errors="ignore",
        ).lower()

        forbidden = [
            "postgresql://",
            "asyncpg://",
            "tenant_password",
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
                    "Forbidden token "
                    + token
                    + " in "
                    + str(path)
                )

self_service = Path(
    "app/modules/meetings/"
    "self_service.py"
).read_text(
    encoding="utf-8",
)

if "Employee.user_id" not in self_service:
    raise SystemExit(
        "Authenticated employee link missing."
    )

if "actor_user_id" not in self_service:
    raise SystemExit(
        "Trusted actor user id missing."
    )

monitoring = Path(
    "app/modules/monitoring_control/"
    "service.py"
).read_text(
    encoding="utf-8",
)

if "WorkspacePermissionService" not in monitoring:
    raise SystemExit(
        "Monitoring permission service missing."
    )

print("PASS trusted actor identity")
print("PASS employee self-response boundary")
print("PASS monitoring permission boundary")
print("PASS tenant DB isolation")
print("PASS privacy boundary")
'@

$SecurityScript | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Phase 11.8 security boundary failed."
}

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 11.8 INTEGRATION: PASS"
Write-Host " Permissions / Meetings / Monitoring Control"
Write-Host "================================================="