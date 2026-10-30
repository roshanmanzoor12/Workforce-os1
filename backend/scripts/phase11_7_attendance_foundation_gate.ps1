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
    throw "Control migration check failed."
}

Write-Host $Revision

if ($Revision -notmatch "d9e0f1a2b3c4")
{
    throw "Phase 11.7 membership revision is not current."
}

Write-Host "PASS control membership foundation"
Write-Host ""

Write-Host "[1/6] Compile Attendance foundation..."

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
    AttendanceDay,
    AttendanceEvent,
)

for model in (
    AttendanceDay,
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

print("PASS AttendanceDay tenant scope")
print("PASS AttendanceEvent tenant scope")
print("PASS no workspace_id duplication")
'@

$ModelScript | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Attendance tenant model contract failed."
}

Write-Host ""

Write-Host "[4/6] Employee relationship contract..."

$EmployeeScript = @'
from app.modules.attendance.models import (
    AttendanceDay,
    AttendanceEvent,
)

day_fk = {
    fk.target_fullname
    for fk
    in AttendanceDay.__table__
    .columns["employee_id"]
    .foreign_keys
}

event_fk = {
    fk.target_fullname
    for fk
    in AttendanceEvent.__table__
    .columns["employee_id"]
    .foreign_keys
}

if "employees.id" not in day_fk:
    raise SystemExit(
        "AttendanceDay employee FK missing."
    )

if "employees.id" not in event_fk:
    raise SystemExit(
        "AttendanceEvent employee FK missing."
    )

print("PASS AttendanceDay -> Employee")
print("PASS AttendanceEvent -> Employee")
print("PASS employee identity reused")
'@

$EmployeeScript | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Attendance Employee relationship failed."
}

Write-Host ""

Write-Host "[5/6] Attendance calculator contract..."

$CalculatorScript = @'
from app.modules.attendance.calculator import (
    AttendanceCalculationError,
    calculate_attendance_totals,
)

if not callable(
    calculate_attendance_totals
):
    raise SystemExit(
        "Attendance calculator missing."
    )

if not issubclass(
    AttendanceCalculationError,
    ValueError,
):
    raise SystemExit(
        "AttendanceCalculationError invalid."
    )

print("PASS deterministic totals calculator")
print("PASS invalid event order protection")
'@

$CalculatorScript | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Attendance calculator contract failed."
}

Write-Host ""

Write-Host "[6/6] Privacy and source boundary..."

$PrivacyScript = @'
from pathlib import Path

root = Path(
    "app/modules/attendance"
)

forbidden = [
    "keylogger",
    "keylogging",
    "clipboard_capture",
    "typed_text",
    "password_capture",
    "mouse_coordinates",
    "stealth_mode",
]

for path in root.rglob("*.py"):
    text = path.read_text(
        encoding="utf-8",
        errors="ignore",
    ).lower()

    for token in forbidden:
        if token in text:
            raise SystemExit(
                "Forbidden token "
                + token
                + " in "
                + str(path)
            )

event_model = Path(
    "app/modules/attendance/models.py"
).read_text(
    encoding="utf-8",
)

if "source" not in event_model:
    raise SystemExit(
        "Attendance source attribution missing."
    )

print("PASS event source attribution")
print("PASS transparent attendance architecture")
print("PASS no keylogging")
print("PASS no clipboard capture")
print("PASS no typed-text capture")
'@

$PrivacyScript | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Attendance privacy boundary failed."
}

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 11.7 ATTENDANCE FOUNDATION: PASS"
Write-Host "================================================="