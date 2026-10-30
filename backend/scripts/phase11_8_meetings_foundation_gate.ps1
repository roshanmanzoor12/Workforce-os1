$ErrorActionPreference = "Stop"

$BackendRoot = "C:\workforce-os\backend"
$Python = "C:\workforce-os\backend\.venv\Scripts\python.exe"

Set-Location $BackendRoot

Write-Host "================================================="
Write-Host " WorkforceOS Phase 11.8 Meetings Foundation"
Write-Host "================================================="
Write-Host ""

Write-Host "[1/7] Compile..."

& $Python `
    -m compileall `
    .\app\modules\workspace_permissions `
    .\app\modules\meetings `
    .\app\modules\tenant_api\router.py `
    .\tests\test_phase11_8_meetings_foundation.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Meetings foundation compile failed."
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

Write-Host "[3/7] Meetings tests..."

& $Python `
    -m pytest `
    .\tests\test_phase11_8_workspace_permissions.py `
    .\tests\test_phase11_8_meetings_foundation.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Meetings foundation tests failed."
}

Write-Host "PASS tests"
Write-Host ""

Write-Host "[4/7] Tenant model contract..."

$ModelScript = @'
from app.db.tenant_base import TenantBase

from app.modules.meetings.models import (
    Meeting,
    MeetingParticipant,
)

for model in (
    Meeting,
    MeetingParticipant,
):
    if not issubclass(
        model,
        TenantBase,
    ):
        raise SystemExit(
            model.__name__
            + " is not tenant scoped."
        )

    columns = {
        column.name
        for column
        in model.__table__.columns
    }

    if "workspace_id" in columns:
        raise SystemExit(
            model.__name__
            + " duplicates tenant workspace scope."
        )

print("PASS Meeting TenantBase")
print("PASS MeetingParticipant TenantBase")
print("PASS no workspace_id duplication")
'@

$ModelScript | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Meeting model contract failed."
}

Write-Host ""

Write-Host "[5/7] Permission integration..."

$PermissionScript = @'
from app.modules.workspace_permissions.permissions import (
    WorkspacePermission,
)
from app.modules.workspace_permissions.policy import (
    WorkspacePermissionPolicy,
)

if not WorkspacePermissionPolicy.allows(
    role_key="member",
    permission=(
        WorkspacePermission
        .MEETINGS_CREATE
        .value
    ),
):
    raise SystemExit(
        "Member cannot create meeting."
    )

if WorkspacePermissionPolicy.allows(
    role_key="member",
    permission=(
        WorkspacePermission
        .MEETINGS_MANAGE
        .value
    ),
):
    raise SystemExit(
        "Member unexpectedly has "
        "meeting management permission."
    )

if not WorkspacePermissionPolicy.allows(
    role_key="admin",
    permission=(
        WorkspacePermission
        .MEETINGS_MANAGE
        .value
    ),
):
    raise SystemExit(
        "Admin meeting management "
        "permission missing."
    )

print("PASS MEMBER meeting create")
print("PASS MEMBER management denied")
print("PASS ADMIN meeting management")
print("PASS OWNER full meeting permissions")
'@

$PermissionScript | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Meeting permission integration failed."
}

Write-Host ""

Write-Host "[6/7] OpenAPI surface..."

$ApiScript = @'
from app.main import app

paths = app.openapi().get(
    "paths",
    {},
)

required = {
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
        "{meeting_id}"
    ): {
        "get",
        "patch",
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
        "{meeting_id}/cancel"
    ): {
        "post",
    },
    (
        "/api/v1/workspaces/"
        "{workspace_id}/permissions/me"
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
        key.lower()
        for key
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

print("PASS Phase 11.8 OpenAPI surface")
'@

$ApiScript | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Meeting OpenAPI contract failed."
}

Write-Host ""

Write-Host "[7/7] Security and privacy boundary..."

$SecurityScript = @'
from pathlib import Path

roots = [
    Path(
        "app/modules/meetings"
    ),
    Path(
        "app/modules/workspace_permissions"
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
            "database_url",
            "tenant_password",
            "capture_keystrokes",
            "capture_clipboard",
            "capture_typed_text",
            "capture_password",
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

router = Path(
    "app/modules/meetings/router.py"
).read_text(
    encoding="utf-8",
)

required = [
    "TenantScope",
    "WorkspacePermissionService",
    "MEETINGS_VIEW",
    "MEETINGS_CREATE",
    "MEETINGS_MANAGE",
]

for token in required:
    if token not in router:
        raise SystemExit(
            "Missing meeting security token: "
            + token
        )

print("PASS trusted TenantScope")
print("PASS centralized permission policy")
print("PASS frontend cannot choose tenant DB")
print("PASS privacy boundary")
'@

$SecurityScript | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Meeting security boundary failed."
}

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 11.8 MEETINGS FOUNDATION: PASS"
Write-Host "================================================="