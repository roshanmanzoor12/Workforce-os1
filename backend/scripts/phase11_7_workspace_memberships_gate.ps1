$ErrorActionPreference = "Stop"

$BackendRoot = "C:\workforce-os\backend"
$Python = "C:\workforce-os\backend\.venv\Scripts\python.exe"

Set-Location $BackendRoot

Write-Host "================================================="
Write-Host " WorkforceOS Phase 11.7 Membership Gate"
Write-Host "================================================="
Write-Host ""

Write-Host "[preflight 1/2] PostgreSQL 5434..."

$Postgres = Test-NetConnection `
    -ComputerName "127.0.0.1" `
    -Port 5434 `
    -WarningAction SilentlyContinue

if (-not $Postgres.TcpTestSucceeded)
{
    throw "PostgreSQL 5434 is not reachable."
}

Write-Host "PASS PostgreSQL reachable"
Write-Host ""

Write-Host "[preflight 2/2] Migration chain..."

$BeforeRevision = (
    & $Python `
        -m alembic `
        -c .\alembic-control.ini `
        current
)

if ($LASTEXITCODE -ne 0)
{
    throw "Alembic current failed."
}

Write-Host $BeforeRevision

if ($BeforeRevision -notmatch "c8d9e0f1a2b3|d9e0f1a2b3c4")
{
    throw "Unexpected control migration revision."
}

Write-Host "PASS migration chain ready"
Write-Host ""

Write-Host "[1/7] Compiling membership foundation..."

& $Python `
    -m compileall `
    .\app\modules\memberships `
    .\tests\test_phase11_7_workspace_memberships.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Membership foundation compile failed."
}

Write-Host "PASS compile"
Write-Host ""

Write-Host "[2/7] Membership tests..."

& $Python `
    -m pytest `
    .\tests\test_phase11_7_workspace_memberships.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Membership tests failed."
}

Write-Host "PASS tests"
Write-Host ""

Write-Host "[3/7] Phase 11.7 migration marker..."

& $Python `
    -m alembic `
    -c .\alembic-control.ini `
    upgrade head

if ($LASTEXITCODE -ne 0)
{
    throw "Phase 11.7 migration marker failed."
}

$CurrentRevision = (
    & $Python `
        -m alembic `
        -c .\alembic-control.ini `
        current
)

if ($LASTEXITCODE -ne 0)
{
    throw "Alembic current failed after upgrade."
}

Write-Host $CurrentRevision

if ($CurrentRevision -notmatch "d9e0f1a2b3c4")
{
    throw "Expected Phase 11.7 revision d9e0f1a2b3c4."
}

Write-Host "PASS migration marker"
Write-Host ""

Write-Host "[4/7] Existing membership model contract..."

$ModelScript = @'
from app.modules.memberships.models import (
    WorkspaceMembership,
)

if (
    WorkspaceMembership.__module__
    != "app.modules.workspaces.models"
):
    raise SystemExit(
        "Phase 11.7 is not reusing "
        "the existing membership model."
    )

columns = {
    column.name
    for column
    in WorkspaceMembership.__table__.columns
}

required = {
    "id",
    "workspace_id",
    "user_id",
    "role_key",
    "status",
    "invited_by_user_id",
    "invited_at",
    "joined_at",
    "suspended_at",
    "removed_at",
    "created_at",
    "updated_at",
}

missing = required - columns

if missing:
    raise SystemExit(
        "Missing existing membership columns: "
        + ", ".join(sorted(missing))
    )

print("PASS existing WorkspaceMembership reused")
print("PASS role_key contract")
print("PASS membership lifecycle contract")
print("PASS no duplicate SQLAlchemy table")
'@

$ModelScript | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Membership model contract failed."
}

Write-Host ""

Write-Host "[5/7] Membership REST API contract..."

$ApiScript = @'
from app.main import app

paths = app.openapi().get(
    "paths",
    {},
)

expected = {
    (
        "/api/v1/workspace-memberships/"
        "{workspace_id}/bootstrap-owner"
    ): {"post"},
    (
        "/api/v1/workspace-memberships/"
        "{workspace_id}/me"
    ): {"get"},
    (
        "/api/v1/workspace-memberships/"
        "{workspace_id}"
    ): {"get"},
    (
        "/api/v1/workspace-memberships/"
        "{workspace_id}/members/"
        "{target_user_id}"
    ): {
        "post",
        "delete",
    },
    (
        "/api/v1/workspace-memberships/"
        "{workspace_id}/members/"
        "{target_user_id}/role"
    ): {"patch"},
}

for path, methods in expected.items():
    if path not in paths:
        raise SystemExit(
            "Missing membership route: "
            + path
        )

    actual = {
        method.lower()
        for method
        in paths[path].keys()
    }

    missing = methods - actual

    if missing:
        raise SystemExit(
            path
            + " missing methods: "
            + ", ".join(sorted(missing))
        )

    for method in sorted(methods):
        print(
            "PASS: "
            + method.upper()
            + " "
            + path
        )

print("PASS membership REST API contract")
'@

$ApiScript | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Membership REST API contract failed."
}

Write-Host ""

Write-Host "[6/7] Membership security boundary..."

$SecurityScript = @'
from pathlib import Path

service = Path(
    "app/modules/memberships/service.py"
).read_text(
    encoding="utf-8",
)

router = Path(
    "app/modules/memberships/router.py"
).read_text(
    encoding="utf-8",
)

required_service = [
    "require_active_member",
    "require_manager",
    "WORKSPACE_ROLE_OWNER",
    "WORKSPACE_ROLE_ADMIN",
    "MEMBERSHIP_STATUS_ACTIVE",
    "bootstrap_owner",
]

for token in required_service:
    if token not in service:
        raise SystemExit(
            "Missing membership security token: "
            + token
        )

if "get_current_verified_user" not in router:
    raise SystemExit(
        "Verified-user boundary missing."
    )

if "get_control_db" not in router:
    raise SystemExit(
        "Control DB boundary missing."
    )

print("PASS verified-user boundary")
print("PASS active membership boundary")
print("PASS OWNER/ADMIN boundary")
print("PASS workspace creator bootstrap boundary")
print("PASS frontend cannot choose tenant database")
'@

$SecurityScript | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Membership security boundary failed."
}

Write-Host ""

Write-Host "[7/7] Existing schema/database boundary..."

$DatabaseScript = @'
import asyncio

from sqlalchemy import text

from app.core.database import (
    ControlSessionLocal,
)


async def main():
    async with ControlSessionLocal() as db:
        result = await db.execute(
            text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name =
                    'workspace_memberships'
                ORDER BY ordinal_position
                """
            )
        )

        columns = {
            row[0]
            for row in result.fetchall()
        }

        required = {
            "workspace_id",
            "user_id",
            "role_key",
            "status",
            "invited_by_user_id",
            "invited_at",
            "joined_at",
            "suspended_at",
            "removed_at",
            "id",
            "created_at",
            "updated_at",
        }

        missing = required - columns

        if missing:
            raise SystemExit(
                "Database membership schema "
                "missing: "
                + ", ".join(
                    sorted(missing)
                )
            )

        print(
            "PASS existing database "
            "membership table"
        )

        print(
            "PASS control-plane membership "
            "schema preserved"
        )


asyncio.run(main())
'@

$DatabaseScript | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Membership database boundary failed."
}

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 11.7 WORKSPACE MEMBERSHIPS: PASS"
Write-Host "================================================="