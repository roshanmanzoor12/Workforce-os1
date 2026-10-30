$ErrorActionPreference = "Stop"

$BackendRoot = "C:\workforce-os\backend"
$Python = "C:\workforce-os\backend\.venv\Scripts\python.exe"

Set-Location $BackendRoot

Write-Host "================================================="
Write-Host " Phase 11.8 Tenant DB Schema Probe"
Write-Host "================================================="
Write-Host ""

Write-Host "[1/3] Tenant revision..."

$Current = (
    & $Python `
        -m alembic `
        -c .\alembic.tenant.ini `
        current
)

if ($LASTEXITCODE -ne 0)
{
    throw "Unable to read tenant revision."
}

Write-Host $Current

if ($Current -notmatch "d3e4f5a6b7c8")
{
    throw "Meeting tenant revision not applied."
}

Write-Host "PASS tenant revision"
Write-Host ""

Write-Host "[2/3] ORM metadata..."

$Metadata = @'
from app.modules.meetings.models import (
    Meeting,
    MeetingParticipant,
)

assert Meeting.__tablename__ == "meetings"

assert (
    MeetingParticipant.__tablename__
    == "meeting_participants"
)

employee_fk = {
    fk.target_fullname
    for fk
    in MeetingParticipant
    .__table__
    .columns["employee_id"]
    .foreign_keys
}

meeting_fk = {
    fk.target_fullname
    for fk
    in MeetingParticipant
    .__table__
    .columns["meeting_id"]
    .foreign_keys
}

assert "employees.id" in employee_fk
assert "meetings.id" in meeting_fk

print("PASS meetings ORM metadata")
print("PASS participant ORM metadata")
print("PASS meeting relationships")
'@

$Metadata | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "ORM metadata probe failed."
}

Write-Host ""

Write-Host "[3/3] Migration metadata..."

$MigrationProbe = @'
from app.modules.meetings.migration_contract import (
    MEETINGS_TENANT_DOWN_REVISION,
    MEETINGS_TENANT_REVISION,
    MEETINGS_TENANT_TABLES,
)

assert (
    MEETINGS_TENANT_REVISION
    == "d3e4f5a6b7c8"
)

assert (
    MEETINGS_TENANT_DOWN_REVISION
    == "c2d3e4f5a6b7"
)

assert MEETINGS_TENANT_TABLES == {
    "meetings",
    "meeting_participants",
}

print("PASS migration revision contract")
print("PASS migration table contract")
'@

$MigrationProbe | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Migration metadata probe failed."
}

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 11.8 TENANT SCHEMA DB PROBE: PASS"
Write-Host "================================================="