$ErrorActionPreference = "Stop"

$BackendRoot = "C:\workforce-os\backend"
$Python = "C:\workforce-os\backend\.venv\Scripts\python.exe"

Set-Location $BackendRoot

Write-Host "================================================="
Write-Host " WorkforceOS Phase 11.7 Tenant REST Gate"
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

Write-Host "[preflight 2/2] Control revision..."

$Revision = (
    & $Python `
        -m alembic `
        -c .\alembic-control.ini `
        current
)

if ($LASTEXITCODE -ne 0)
{
    throw "Control migration check failed."
}

Write-Host $Revision

if ($Revision -notmatch "d9e0f1a2b3c4")
{
    throw "Phase 11.7 membership revision missing."
}

Write-Host "PASS control revision"
Write-Host ""

Write-Host "[1/6] Compile tenant REST surface..."

& $Python `
    -m compileall `
    .\app\modules\tenant_api `
    .\app\modules\employees\router.py `
    .\app\modules\attendance\router.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Tenant REST compile failed."
}

Write-Host "PASS compile"
Write-Host ""

Write-Host "[2/6] Import application..."

& $Python `
    -c "from app.main import app; print('PASS app.main import')"

if ($LASTEXITCODE -ne 0)
{
    throw "Application import failed."
}

Write-Host ""

Write-Host "[3/6] REST contract tests..."

& $Python `
    -m pytest `
    .\tests\test_phase11_7_employee_rest_routes.py `
    .\tests\test_phase11_7_attendance_rest_routes.py `
    .\tests\test_phase11_7_tenant_rest_security.py `
    .\tests\test_phase11_7_tenant_rest_domain_contract.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Tenant REST tests failed."
}

Write-Host "PASS REST tests"
Write-Host ""

Write-Host "[4/6] OpenAPI contract..."

$ApiScript = @'
from app.main import app

paths = app.openapi().get(
    "paths",
    {},
)

required = [
    "/api/v1/workspaces/{workspace_id}/departments",
    "/api/v1/workspaces/{workspace_id}/teams",
    "/api/v1/workspaces/{workspace_id}/employees",
    (
        "/api/v1/workspaces/{workspace_id}/"
        "attendance/records"
    ),
    (
        "/api/v1/workspaces/{workspace_id}/"
        "attendance/employees/{employee_id}/events"
    ),
]

for path in required:
    if path not in paths:
        raise SystemExit(
            "Missing REST route: "
            + path
        )

    print(
        "PASS "
        + path
    )

print("PASS tenant REST OpenAPI surface")
'@

$ApiScript | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "OpenAPI contract failed."
}

Write-Host ""

Write-Host "[5/6] Tenant security boundary..."

$SecurityScript = @'
from pathlib import Path

dependency_path = Path(
    "app/modules/tenant_api/"
    "dependencies.py"
)

dependency = dependency_path.read_text(
    encoding="utf-8",
)

required = [
    "get_current_verified_user",
    "get_control_db",
    "WorkspaceMembershipRepository",
    "get_active_for_user",
    "MEMBERSHIP_STATUS_ACTIVE",
    "get_registered_tenant_session_resolver",
    "tenant_session = await resolver",
    "AuthorizedTenantContext",
    "AsyncSession",
]

for token in required:
    if token not in dependency:
        raise SystemExit(
            "Missing tenant security token: "
            + token
        )

for forbidden in [
    "authorized_tenant_session",
    "request.state",
    "postgresql://",
    "asyncpg://",
]:
    if forbidden in dependency:
        raise SystemExit(
            "Forbidden stale tenant dependency token: "
            + forbidden
        )

routers = [
    Path(
        "app/modules/employees/router.py"
    ),
    Path(
        "app/modules/attendance/router.py"
    ),
]

for path in routers:
    text = path.read_text(
        encoding="utf-8",
    ).lower()

    forbidden = [
        "postgresql://",
        "asyncpg://",
        "database_url",
        "connection_string",
        "tenant_password",
    ]

    for token in forbidden:
        if token in text:
            raise SystemExit(
                "Forbidden routing token "
                + token
                + " in "
                + str(path)
            )

print("PASS verified user boundary")
print("PASS control DB boundary")
print("PASS active membership boundary")
print("PASS registered tenant resolver boundary")
print("PASS backend-controlled tenant session")
print("PASS frontend cannot provide database URL")
'@

$SecurityScript | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Tenant security boundary failed."
}

Write-Host ""

Write-Host "[6/6] Domain isolation..."

$DomainScript = @'
from app.modules.employees.models import (
    Department,
    Employee,
    Team,
)
from app.modules.attendance.models import (
    AttendanceEvent,
    AttendanceRecord,
)

models = [
    Department,
    Team,
    Employee,
    AttendanceRecord,
    AttendanceEvent,
]

for model in models:
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

print("PASS Department tenant isolation")
print("PASS Team tenant isolation")
print("PASS Employee tenant isolation")
print("PASS Attendance tenant isolation")
print("PASS no workspace_id duplication")
'@

$DomainScript | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Tenant domain isolation failed."
}

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 11.7 TENANT REST SURFACE: PASS"
Write-Host "================================================="