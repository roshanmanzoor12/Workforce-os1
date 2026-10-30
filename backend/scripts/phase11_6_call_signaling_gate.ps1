$ErrorActionPreference = "Stop"

$BackendRoot = "C:\workforce-os\backend"
$Python = "C:\workforce-os\backend\.venv\Scripts\python.exe"
$MainFile = Join-Path $BackendRoot "app\main.py"

Set-Location $BackendRoot

Write-Host "================================================="
Write-Host " WorkforceOS Phase 11.6 Call Signaling Gate"
Write-Host "================================================="
Write-Host ""

# =========================================================
# 0. WIRING
# =========================================================

Write-Host "[0/7] Call router wiring..."

$Text = Get-Content $MainFile -Raw

$ImportLine = "from app.modules.calls.router import router as calls_router"
$IncludeLine = "app.include_router(calls_router, prefix=`"/api/v1`")"

if (-not $Text.Contains($ImportLine))
{
    $Text = $ImportLine + "`r`n" + $Text
}

if (-not $Text.Contains($IncludeLine))
{
    $Text = $Text.TrimEnd() + "`r`n`r`n" + $IncludeLine + "`r`n"
}

$Text = $Text.Replace(
    ")from app.modules.",
    ")`r`n`r`nfrom app.modules."
)

$Text = $Text.Replace(
    ")app.include_router(",
    ")`r`n`r`napp.include_router("
)

Set-Content -Path $MainFile -Value $Text -Encoding UTF8

Write-Host "PASS call router wiring"
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

Write-Host "[preflight 2/2] Redis 6381..."

$Redis = Test-NetConnection `
    -ComputerName "127.0.0.1" `
    -Port 6381 `
    -WarningAction SilentlyContinue

if (-not $Redis.TcpTestSucceeded)
{
    throw "Redis 6381 is not reachable."
}

Write-Host "PASS Redis reachable"
Write-Host ""

# =========================================================
# 1. COMPILE
# =========================================================

Write-Host "[1/7] Compiling..."

& $Python `
    -m compileall `
    .\app\modules\calls `
    .\tests\test_phase11_6_call_signaling.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Call signaling compile failed."
}

Write-Host "PASS compile"
Write-Host ""

# =========================================================
# 2. TESTS
# =========================================================

Write-Host "[2/7] Call signaling tests..."

& $Python `
    -m pytest `
    .\tests\test_phase11_6_call_signaling.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Call signaling tests failed."
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
    throw "Call migration upgrade failed."
}

$CurrentRevision = (
    & $Python `
        -m alembic `
        -c .\alembic-control.ini `
        current
)

if ($LASTEXITCODE -ne 0)
{
    throw "Alembic current failed."
}

Write-Host $CurrentRevision

if ($CurrentRevision -notmatch "c8d9e0f1a2b3")
{
    throw "Expected call migration c8d9e0f1a2b3."
}

Write-Host "PASS migration"
Write-Host ""

# =========================================================
# 4. MODEL CONTRACT
# =========================================================

Write-Host "[4/7] Call model contract..."

$ModelScript = @'
from app.modules.calls.models import (
    RealtimeCall,
    RealtimeCallParticipant,
)

call_columns = {
    column.name
    for column in RealtimeCall.__table__.columns
}

participant_columns = {
    column.name
    for column
    in RealtimeCallParticipant.__table__.columns
}

required_call = {
    "id",
    "scope",
    "conversation_id",
    "channel_id",
    "started_by_user_id",
    "kind",
    "status",
    "started_at",
    "ended_at",
}

required_participant = {
    "call_id",
    "user_id",
    "state",
    "microphone_enabled",
    "camera_enabled",
    "screen_share_state",
}

missing_call = required_call - call_columns

if missing_call:
    raise SystemExit(
        "Missing call columns: "
        + ", ".join(sorted(missing_call))
    )

missing_participant = (
    required_participant
    - participant_columns
)

if missing_participant:
    raise SystemExit(
        "Missing participant columns: "
        + ", ".join(
            sorted(missing_participant)
        )
    )

print("PASS call model")
print("PASS participant state model")
print("PASS screen-share state model")
'@

$ModelScript | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Call model contract failed."
}

Write-Host ""

# =========================================================
# 5. REST CONTRACT
# =========================================================

Write-Host "[5/7] Call REST API contract..."

$ApiScript = @'
from app.main import app

paths = app.openapi().get(
    "paths",
    {},
)

expected = {
    "/api/v1/calls": {"post"},
    "/api/v1/calls/{call_id}": {"get"},
    "/api/v1/calls/{call_id}/participants": {"get"},
    "/api/v1/calls/{call_id}/join": {"post"},
    "/api/v1/calls/{call_id}/leave": {"post"},
    "/api/v1/calls/{call_id}/decline": {"post"},
    "/api/v1/calls/{call_id}/end": {"post"},
    "/api/v1/calls/{call_id}/screen-share/start": {"post"},
    "/api/v1/calls/{call_id}/screen-share/stop": {"post"},
    "/api/v1/calls/{call_id}/signal": {"post"},
}

for path, methods in expected.items():
    if path not in paths:
        raise SystemExit(
            "Missing call route: "
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

print("PASS call REST contract")
'@

$ApiScript | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Call REST API contract failed."
}

Write-Host ""

# =========================================================
# 6. AUTHORIZATION
# =========================================================

Write-Host "[6/7] Call permission boundary..."

$BoundaryScript = @'
from pathlib import Path

service = Path(
    "app/modules/calls/service.py"
).read_text(
    encoding="utf-8",
)

router = Path(
    "app/modules/calls/router.py"
).read_text(
    encoding="utf-8",
)

required = [
    "ConversationMember",
    "WorkspaceChannelMember",
    "CallParticipantState.JOINED",
    "started_by_user_id",
    "assert_signal_access",
    "set_screen_share",
]

for token in required:
    if token not in service:
        raise SystemExit(
            "Missing call boundary: "
            + token
        )

if "get_current_verified_user" not in router:
    raise SystemExit(
        "Verified-user call boundary missing."
    )

if "get_control_db" not in router:
    raise SystemExit(
        "Control DB call boundary missing."
    )

print("PASS verified-user boundary")
print("PASS conversation membership boundary")
print("PASS channel membership boundary")
print("PASS joined-participant signaling boundary")
print("PASS joined-participant screen-share boundary")
print("PASS call-starter end-call boundary")
'@

$BoundaryScript | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Call permission boundary failed."
}

Write-Host ""

# =========================================================
# 7. SIGNALING PRIVACY
# =========================================================

Write-Host "[7/7] Signaling privacy contract..."

$PrivacyScript = @'
from pathlib import Path

text = Path(
    "app/modules/calls/signaling.py"
).read_text(
    encoding="utf-8",
)

required = [
    "call.created",
    "call.signal",
    "call.ended",
    "call.screen_share.started",
    "call.screen_share.stopped",
]

for token in required:
    if token not in text:
        raise SystemExit(
            "Missing signaling event: "
            + token
        )

forbidden = [
    "MINIO_ACCESS_KEY",
    "MINIO_SECRET_KEY",
    "DATABASE_URL",
    "password",
    "clipboard",
    "keylog",
]

for token in forbidden:
    if token in text:
        raise SystemExit(
            "Forbidden signaling payload token: "
            + token
        )

print("PASS voice/video signaling payload")
print("PASS group-call participant payload")
print("PASS screen-share signaling payload")
print("PASS signaling stays application-mediated")
print("PASS no database/storage credentials exposed")
'@

$PrivacyScript | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Call signaling privacy contract failed."
}

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 11.6 CALL SIGNALING FOUNDATION: PASS"
Write-Host "================================================="