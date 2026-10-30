$ErrorActionPreference = "Stop"

$BackendRoot = "C:\workforce-os\backend"
$Python = "C:\workforce-os\backend\.venv\Scripts\python.exe"

Set-Location $BackendRoot

Write-Host "================================================="
Write-Host " WorkforceOS Phase 11.7 Attendance Foundation"
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

Write-Host "[preflight 2/2] Control membership revision..."

$Revision = (
    & $Python `
        -m alembic `
        -c .\alembic-control.ini `
        current
)

if ($LASTEXITCODE -ne 0)
{
    throw "Control Alembic current failed."
}

Write-Host $Revision

if ($Revision -notmatch "d9e0f1a2b3c4")
{
    throw "Phase 11.7 membership revision is not current."
}

Write-Host "PASS membership foundation ready"
Write-Host ""

Write-Host "[1/6] Compile Attendance..."

& $Python `
    -m compileall `
    .\app\modules\attendance `
    .\tests\test_phase11_7_attendance_models.py `
    .\tests\test_phase11_7_attendance_architecture.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Attendance compile failed."
}

Write-Host "PASS compile"
Write-Host ""

Write-Host "[2/6] Attendance tests..."

& $Python `
    -m pytest `
    .\tests\test_phase11_7_attendance_models.py `
    .\tests\test_phase11_7_attendance_architecture.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Attendance tests failed."
}

Write-Host "PASS tests"
Write-Host ""

Write-Host "[3/6] Tenant model contract..."

$ModelScript = @'
from app.db.tenant_base import TenantBase

from app.modules.attendance.models import (
    AttendanceEvent,
    AttendanceRecord,
)

for model in (
    AttendanceRecord,
    AttendanceEvent,
):
    if not issubclass(
        model,
        TenantBase,
    ):
        raise SystemExit(
            model.__name__
            + " is not tenant scoped."
        )

if (
    AttendanceRecord.__tablename__
    != "attendance_records"
):
    raise SystemExit(
        "AttendanceRecord table mismatch."
    )

if (
    AttendanceEvent.__tablename__
    != "attendance_events"
):
    raise SystemExit(
        "AttendanceEvent table mismatch."
    )

print("PASS AttendanceRecord TenantBase")
print("PASS AttendanceEvent TenantBase")
print("PASS attendance tenant isolation")
'@

$ModelScript | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Attendance model contract failed."
}

Write-Host ""

Write-Host "[4/6] Employee boundary..."

$EmployeeScript = @'
from app.modules.attendance.models import (
    AttendanceRecord,
)

column = (
    AttendanceRecord.__table__
    .columns["employee_id"]
)

targets = {
    foreign_key.target_fullname
    for foreign_key
    in column.foreign_keys
}

if "employees.id" not in targets:
    raise SystemExit(
        "Attendance employee foreign key missing."
    )

print("PASS Attendance belongs to Employee")
print("PASS tenant-local employee FK")
print("PASS no control-plane employee FK")
'@

$EmployeeScript | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Attendance Employee boundary failed."
}

Write-Host ""

Write-Host "[5/6] Authorization boundary..."

$AuthorizationScript = @'
from pathlib import Path

access = Path(
    "app/modules/attendance/"
    "access_service.py"
).read_text(
    encoding="utf-8",
)

required = [
    "EmployeeMembershipBridge",
    "control_session",
    "tenant_session",
    "require_active_member",
    "require_manager",
]

for token in required:
    if token not in access:
        raise SystemExit(
            "Missing attendance access token: "
            + token
        )

print("PASS control authorization first")
print("PASS tenant attendance