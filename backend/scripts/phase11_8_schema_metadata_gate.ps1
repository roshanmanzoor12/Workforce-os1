$ErrorActionPreference = "Stop"

$BackendRoot = "C:\workforce-os\backend"
$Python = "C:\workforce-os\backend\.venv\Scripts\python.exe"

Set-Location $BackendRoot

Write-Host "================================================="
Write-Host " Phase 11.8 Schema Metadata Gate"
Write-Host "================================================="
Write-Host ""

$Script = @'
from app.modules.meetings.contract import (
    MEETING_PARTICIPANT_REQUIRED_COLUMNS,
    MEETING_REQUIRED_COLUMNS,
)
from app.modules.meetings.models import (
    Meeting,
    MeetingParticipant,
)

if Meeting.__tablename__ != "meetings":
    raise SystemExit(
        "Meeting table name mismatch."
    )

if (
    MeetingParticipant.__tablename__
    != "meeting_participants"
):
    raise SystemExit(
        "MeetingParticipant table name mismatch."
    )

meeting_columns = {
    column.name
    for column
    in Meeting.__table__.columns
}

missing = (
    MEETING_REQUIRED_COLUMNS
    - meeting_columns
)

if missing:
    raise SystemExit(
        "Meeting missing columns: "
        + ", ".join(
            sorted(missing)
        )
    )

participant_columns = {
    column.name
    for column
    in MeetingParticipant.__table__.columns
}

missing = (
    MEETING_PARTICIPANT_REQUIRED_COLUMNS
    - participant_columns
)

if missing:
    raise SystemExit(
        "MeetingParticipant missing columns: "
        + ", ".join(
            sorted(missing)
        )
    )

for model in (
    Meeting,
    MeetingParticipant,
):
    columns = {
        column.name
        for column
        in model.__table__.columns
    }

    if "workspace_id" in columns:
        raise SystemExit(
            model.__name__
            + " duplicates tenant scope."
        )

employee_targets = {
    fk.target_fullname
    for fk
    in MeetingParticipant
    .__table__
    .columns["employee_id"]
    .foreign_keys
}

if "employees.id" not in employee_targets:
    raise SystemExit(
        "Participant employee FK missing."
    )

meeting_targets = {
    fk.target_fullname
    for fk
    in MeetingParticipant
    .__table__
    .columns["meeting_id"]
    .foreign_keys
}

if "meetings.id" not in meeting_targets:
    raise SystemExit(
        "Participant meeting FK missing."
    )

print("PASS meetings metadata")
print("PASS meeting_participants metadata")
print("PASS employee FK")
print("PASS meeting FK")
print("PASS tenant isolation")
'@

$Script | & $Python -

if (
    $LASTEXITCODE -ne 0
)
{
    throw "Phase 11.8 metadata gate failed."
}

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 11.8 SCHEMA METADATA: PASS"
Write-Host "================================================="