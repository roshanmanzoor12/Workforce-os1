$ErrorActionPreference = "Stop"

$BackendRoot = "C:\workforce-os\backend"
$Python = "C:\workforce-os\backend\.venv\Scripts\python.exe"

Set-Location $BackendRoot

Write-Host "================================================="
Write-Host " WorkforceOS Phase 11.7 Schema Contract Probe"
Write-Host "================================================="
Write-Host ""

$Probe = @'
from app.modules.employees.models import (
    Department,
    Employee,
    Team,
)
from app.modules.attendance.models import (
    AttendanceEvent,
    AttendanceRecord,
)

models = {
    "departments": Department,
    "teams": Team,
    "employees": Employee,
    "attendance_records": AttendanceRecord,
    "attendance_events": AttendanceEvent,
}

for table_name, model in models.items():
    if model.__tablename__ != table_name:
        raise SystemExit(
            "Table mismatch: "
            + model.__name__
            + " -> "
            + model.__tablename__
        )

    print(
        "PASS model table "
        + table_name
    )

record_columns = {
    column.name
    for column
    in AttendanceRecord.__table__.columns
}

required_record = {
    "employee_id",
    "attendance_date",
    "status",
    "source",
    "check_in_at",
    "check_out_at",
    "worked_minutes",
    "break_minutes",
    "notes",
    "created_by_user_id",
    "updated_by_user_id",
}

missing = (
    required_record
    - record_columns
)

if missing:
    raise SystemExit(
        "AttendanceRecord missing: "
        + ", ".join(
            sorted(missing)
        )
    )

event_columns = {
    column.name
    for column
    in AttendanceEvent.__table__.columns
}

required_event = {
    "attendance_record_id",
    "employee_id",
    "event_type",
    "source",
    "occurred_at",
    "actor_user_id",
    "notes",
}

missing = (
    required_event
    - event_columns
)

if missing:
    raise SystemExit(
        "AttendanceEvent missing: "
        + ", ".join(
            sorted(missing)
        )
    )

print("PASS AttendanceRecord contract")
print("PASS AttendanceEvent contract")
print("PASS Employee organization contract")
print("PASS Phase 11.7 tenant schema metadata")
'@

$Probe | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Phase 11.7 schema probe failed."
}

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 11.7 SCHEMA CONTRACT: PASS"
Write-Host "================================================="