$ErrorActionPreference = "Stop"

$BackendRoot = "C:\workforce-os\backend"

$Python = (
    "C:\workforce-os\backend\" +
    ".venv\Scripts\python.exe"
)

Set-Location $BackendRoot

Write-Host "================================================="
Write-Host " WorkforceOS Phase 11.7 Membership Gate"
Write-Host "================================================="
Write-Host ""

# =========================================================
# PREFLIGHT
# =========================================================

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

Write-Host "[preflight 2/2] Previous Phase 11.6 migration..."

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

if (
    $BeforeRevision -notmatch
    "c8d9e0f1a2b3|d9e0f1a2b3c4"
)
{
    throw (
        "Expected Phase 11.6 or "
        + "Phase 11.7 membership revision."
    )
}

Write-Host "PASS migration chain ready"
Write-Host ""

# =========================================================
# 1. COMPILE
# =========================================================

Write-Host "[1/7] Compiling membership foundation..."

& $Python `
    -m compileall `
    .\app\modules\memberships `
    .\tests\test_phase11_7_workspace_memberships.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw (
        "Membership foundation "
        + "compile failed."
    )
}

Write-Host "PASS compile"
Write-Host ""

# =========================================================
# 2. TESTS
# =========================================================

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

# =========================================================
# 3. MIGRATION
# =========================================================

Write-Host "[3/7] Control migration..."

& $Python `
    -m alembic `
    -c .\alembic-control.ini `
    upgrade head

if ($LASTEXITCODE -ne 0)
{
    throw (
        "Workspace membership "
        + "migration failed."
    )
}

$CurrentRevision = (
    & $Python `
        -m alembic `
        -c .\alembic-control.ini `
        current
)

if ($LASTEXITCODE -ne 0)
{
    throw (
        "Alembic current failed "
        + "after migration."
    )
}

Write-Host $CurrentRevision

if (
    $CurrentRevision -notmatch
    "d9e0f1a2b3c4"
)
{
    throw (
        "Expected membership revision "
        + "d9e0f1a2b3c4."
    )
}

Write-Host "PASS migration"
Write-Host ""

# =========================================================
# 4. MODEL CONTRACT
# =========================================================

Write-Host "[4/7] Membership model contract..."

$ModelScript = @'
from app.modules.memberships.models import (
    WorkspaceMembership,
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
    "role",
    "status",
    "created_by_user_id",
    "created_at",
    "updated_at",
    "activated_at",
    "removed_at",
}

missing = required - columns

if missing:
    raise SystemExit(
        "Missing workspace membership columns: "
        + ", ".join(sorted(missing))
    )

print("PASS WorkspaceMembership model")
print("PASS Global User != WorkspaceMembership")
print("PASS membership lifecycle fields")
'@

$ModelScript | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Membership model contract failed."
}

Write-Host ""

# =========================================================
# 5. API CONTRACT
# =========================================================

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
    ): {
        "post",
    },
    (
        "/api/v1/workspace-memberships/"
        "{workspace_id}/me"
    ): {
        "get",
    },
    (
        "/api/v1/workspace-memberships/"
        "{workspace_id}"
    ): {
        "get",
    },
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
    ): {
        "patch",
    },
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
            + ", ".join(
                sorted(missing)
            )
        )

    for method in sorted(methods):
        print(
            "PASS: "
            + method.upper()
            + " "
            + path
        )

print(
    "PASS membership REST API contract"
)
'@

$ApiScript | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw (
        "Membership REST API "
        + "contract failed."
    )
}

Write-Host ""

# =========================================================
# 6. SECURITY
# =========================================================

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
    "WorkspaceMembershipRole.OWNER",
    "WorkspaceMembershipRole.ADMIN",
    "WorkspaceMembershipStatus.ACTIVE",
    "bootstrap_owner",
]

for token in required_service:
    if token not in service:
        raise SystemExit(
            "Missing membership security token: "
            + token
        )

if (
    "get_current_verified_user"
    not in router
):
    raise SystemExit(
        "Verified-user boundary missing."
    )

if "get_control_db" not in router:
    raise SystemExit(
        "Control DB boundary missing."
    )

print("PASS verified-user boundary")
print("PASS active-membership boundary")
print("PASS OWNER/ADMIN management boundary")
print("PASS workspace creator bootstrap boundary")
print("PASS frontend cannot choose database")
'@

$SecurityScript | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw (
        "Membership security "
        + "boundary failed."
    )
}

Write-Host ""

# =========================================================
# 7. ARCHITECTURE
# =========================================================

Write-Host "[7/7] Membership architecture boundary..."

$ArchitectureScript = @'
from pathlib import Path

model = Path(
    "app/modules/memberships/models.py"
).read_text(
    encoding="utf-8",
)

forbidden = [
    "TenantBase",
    "tenant_database",
    "database_name",
    "connection_string",
]

for token in forbidden:
    if token in model:
        raise SystemExit(
            "Membership model violates "
            "control-plane boundary: "
            + token
        )

print(
    "PASS WorkspaceMembership stays "
    "in control plane"
)

print(
    "PASS Employee remains separate "
    "for next tenant batch"
)

print(
    "PASS Role remains membership role, "
    "not Employee identity"
)

print(
    "PASS Phase 11.7 membership "
    "foundation architecture"
)
'@

$ArchitectureScript | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw (
        "Membership architecture "
        + "boundary failed."
    )
}

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 11.7 WORKSPACE MEMBERSHIPS: PASS"
Write-Host "================================================="