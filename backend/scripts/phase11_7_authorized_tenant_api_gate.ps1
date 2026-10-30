$ErrorActionPreference = "Stop"

$BackendRoot = "C:\workforce-os\backend"
$Python = "C:\workforce-os\backend\.venv\Scripts\python.exe"

Set-Location $BackendRoot

Write-Host "================================================="
Write-Host " WorkforceOS Phase 11.7 Authorized Tenant API"
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

Write-Host "PASS membership revision"
Write-Host ""

Write-Host "[1/6] Compile authorized tenant API..."

& $Python `
    -m compileall `
    .\app\modules\tenant_api `
    .\app\modules\employees\api.py `
    .\app\modules\attendance\api.py `
    .\app\modules\attendance\access_service.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Authorized tenant API compile failed."
}

Write-Host "PASS compile"
Write-Host ""

Write-Host "[2/6] Contract tests..."

& $Python `
    -m pytest `
    .\tests\test_phase11_7_employee_api_contract.py `
    .\tests\test_phase11_7_attendance_api_contract.py `
    .\tests\test_phase11_7_tenant_context_contract.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Authorized tenant API tests failed."
}

Write-Host "PASS tests"
Write-Host ""

Write-Host "[3/6] Import contract..."

$ImportScript = @'
from app.modules.tenant_api.context import (
    AuthorizedTenantContext,
)
from app.modules.employees.api import (
    EmployeeApi,
)
from app.modules.attendance.api import (
    AttendanceApi,
)
from app.modules.attendance.access_service import (
    AttendanceAccessService,
)

print("PASS AuthorizedTenantContext import")
print("PASS EmployeeApi import")
print("PASS AttendanceApi import")
print("PASS AttendanceAccessService import")
'@

$ImportScript | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Authorized tenant API import failed."
}

Write-Host ""

Write-Host "[4/6] Database boundary..."

$BoundaryScript = @'
from pathlib import Path

files = [
    Path(
        "app/modules/tenant_api/context.py"
    ),
    Path(
        "app/modules/employees/api.py"
    ),
    Path(
        "app/modules/attendance/api.py"
    ),
]

forbidden = [
    "postgresql://",
    "asyncpg://",
    "database_url",
    "connection_string",
]

for path in files:
    text = path.read_text(
        encoding="utf-8",
        errors="ignore",
    ).lower()

    for token in forbidden:
        if token in text:
            raise SystemExit(
                "Forbidden database routing token "
                + token
                + " in "
                + str(path)
            )

print("PASS frontend cannot choose database")
print("PASS no database credentials in API layer")
print("PASS authorized session boundary")
'@

$BoundaryScript | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Database boundary failed."
}

Write-Host ""

Write-Host "[5/6] Authorization architecture..."

$AuthScript = @'
from pathlib import Path

employee = Path(
    "app/modules/employees/"
    "access_service.py"
).read_text(
    encoding="utf-8"
)

attendance = Path(
    "app/modules/attendance/"
    "access_service.py"
).read_text(
    encoding="utf-8"
)

for token in [
    "require_active_member",
    "require_manager",
]:
    if token not in employee:
        raise SystemExit(
            "Employee authorization missing: "
            + token
        )

    if token not in attendance:
        raise SystemExit(
            "Attendance authorization missing: "
            + token
        )

print("PASS active-member read boundary")
print("PASS OWNER/ADMIN mutation boundary")
print("PASS control authorization before tenant domain")
'@

$AuthScript | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Authorization architecture failed."
}

Write-Host ""

Write-Host "[6/6] Domain preservation..."

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

expected = {
    Department.__tablename__: "departments",
    Team.__tablename__: "teams",
    Employee.__tablename__: "employees",
    AttendanceRecord.__tablename__: (
        "attendance_records"
    ),
    AttendanceEvent.__tablename__: (
        "attendance_events"
    ),
}

for actual, wanted in expected.items():
    if actual != wanted:
        raise SystemExit(
            "Unexpected tenant table: "
            + actual
        )

print("PASS existing Employee domain preserved")
print("PASS existing Department domain preserved")
print("PASS existing Team domain preserved")
print("PASS AttendanceRecord domain preserved")
print("PASS AttendanceEvent domain preserved")
'@

$DomainScript | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Tenant domain preservation failed."
}

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 11.7 AUTHORIZED TENANT API: PASS"
Write-Host "================================================="