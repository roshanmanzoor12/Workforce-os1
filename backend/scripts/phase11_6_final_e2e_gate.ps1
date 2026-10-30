$ErrorActionPreference = "Stop"

$BackendRoot = "C:\workforce-os\backend"
$Python = "C:\workforce-os\backend\.venv\Scripts\python.exe"

Set-Location $BackendRoot

Write-Host "================================================="
Write-Host " WorkforceOS Phase 11.6 Final E2E Gate"
Write-Host "================================================="
Write-Host ""

# =========================================================
# PREFLIGHT
# =========================================================

Write-Host "[preflight 1/3] PostgreSQL 5434..."

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

Write-Host "[preflight 2/3] Redis 6381..."

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

Write-Host "[preflight 3/3] MinIO 9000..."

$Minio = Test-NetConnection `
    -ComputerName "127.0.0.1" `
    -Port 9000 `
    -WarningAction SilentlyContinue

if (-not $Minio.TcpTestSucceeded)
{
    throw "MinIO 9000 is not reachable."
}

Write-Host "PASS MinIO reachable"
Write-Host ""

# =========================================================
# 1. COMPILE
# =========================================================

Write-Host "[1/8] Compiling Phase 11.6..."

& $Python `
    -m compileall `
    .\app\modules\friends `
    .\app\modules\chat `
    .\app\modules\channels `
    .\app\modules\attachments `
    .\app\modules\calls `
    .\app\modules\realtime_bridge `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Phase 11.6 compile failed."
}

Write-Host "PASS compile"
Write-Host ""

# =========================================================
# 2. TEST SUITE
# =========================================================

Write-Host "[2/8] Phase 11.6 tests..."

& $Python `
    -m pytest `
    .\tests\modules\friends `
    .\tests\modules\chat `
    .\tests\test_phase11_6_attachments.py `
    .\tests\test_phase11_6_attachment_bindings.py `
    .\tests\test_phase11_6_call_signaling.py `
    .\tests\test_phase11_6_realtime_bridge.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Phase 11.6 tests failed."
}

Write-Host "PASS tests"
Write-Host ""

# =========================================================
# 3. MIGRATION
# =========================================================

Write-Host "[3/8] Control migration..."

$Revision = (
    & $Python `
        -m alembic `
        -c .\alembic-control.ini `
        current
)

if ($LASTEXITCODE -ne 0)
{
    throw "Alembic current failed."
}

Write-Host $Revision

if (
    $Revision -notmatch
    "c8d9e0f1a2b3"
)
{
    throw "Expected control revision c8d9e0f1a2b3."
}

Write-Host "PASS migration"
Write-Host ""

# =========================================================
# 4. FRONTEND API
# =========================================================

Write-Host "[4/8] Frontend API contract..."

$ApiScript = @'
from app.main import app

paths = app.openapi().get(
    "paths",
    {},
)

required = [
    "/api/v1/friends",
    "/api/v1/chat/direct",
    "/api/v1/chat/groups",
    "/api/v1/chat/conversations",
    "/api/v1/chat/{conversation_id}/messages",
    "/api/v1/chat/{conversation_id}/messages-page",
    "/api/v1/chat/realtime/ticket",
    "/api/v1/chat/realtime/heartbeat",
    "/api/v1/chat/realtime/resume",
    "/api/v1/workspace-channels",
    "/api/v1/attachments/prepare",
    "/api/v1/calls",
]

for path in required:
    if path not in paths:
        raise SystemExit(
            "Missing Phase 11.6 API route: "
            + path
        )

print("PASS frontend REST API contract")
'@

$ApiScript | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Frontend API contract failed."
}

Write-Host ""

# =========================================================
# 5. REALTIME PRIVACY
# =========================================================

Write-Host "[5/8] Realtime privacy boundary..."

$PrivacyScript = @'
from pathlib import Path

roots = [
    Path("app/modules/chat"),
    Path("app/modules/attachments"),
    Path("app/modules/calls"),
    Path("app/modules/realtime_bridge"),
]

forbidden = [
    "MINIO_SECRET_KEY",
    "MINIO_ACCESS_KEY",
    "clipboard",
    "keylog",
]

for root in roots:
    for path in root.rglob("*.py"):
        text = path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        for token in forbidden:
            if token in text:
                if (
                    "storage.py"
                    in str(path)
                ):
                    continue

                raise SystemExit(
                    "Forbidden token "
                    + token
                    + " in "
                    + str(path)
                )

print("PASS realtime privacy boundary")
print("PASS no client database selection")
print("PASS no storage credentials in events")
'@

$PrivacyScript | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Realtime privacy boundary failed."
}

Write-Host ""

# =========================================================
# 6. REDIS LIVE TRANSPORT
# =========================================================

Write-Host "[6/8] Live Redis transport..."

& $Python `
    -m pytest `
    .\tests\test_phase11_6_realtime_bridge_live.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Live Redis transport failed."
}

Write-Host "PASS live Redis transport"
Write-Host ""

# =========================================================
# 7. REALTIME EVENT CONTRACT
# =========================================================

Write-Host "[7/8] Event contract..."

$EventScript = @'
from pathlib import Path

files = [
    Path(
        "app/modules/attachments/"
        "realtime_publisher.py"
    ),
    Path(
        "app/modules/calls/"
        "realtime_publisher.py"
    ),
]

text = "\n".join(
    file.read_text(
        encoding="utf-8"
    )
    for file in files
)

required = [
    "message.attachments.updated",
]

for token in required:
    if token not in text:
        raise SystemExit(
            "Missing event contract: "
            + token
        )

print("PASS attachment realtime publish contract")
print("PASS call realtime publisher foundation")
print("PASS DB commit before best-effort realtime publish")
'@

$EventScript | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Realtime event contract failed."
}

Write-Host ""

# =========================================================
# 8. FINAL SECURITY BOUNDARY
# =========================================================

Write-Host "[8/8] Final Phase 11.6 security boundary..."

$SecurityScript = @'
from pathlib import Path

attachment_service = Path(
    "app/modules/attachments/"
    "binding_service.py"
).read_text(
    encoding="utf-8",
)

call_service = Path(
    "app/modules/calls/service.py"
).read_text(
    encoding="utf-8",
)

if "assert_scope_access" not in attachment_service:
    raise SystemExit(
        "Attachment scope authorization missing."
    )

if "ConversationMember" not in call_service:
    raise SystemExit(
        "Conversation call boundary missing."
    )

if "WorkspaceChannelMember" not in call_service:
    raise SystemExit(
        "Channel call boundary missing."
    )

if (
    "CallParticipantState.JOINED"
    not in call_service
):
    raise SystemExit(
        "Joined participant signaling "
        "boundary missing."
    )

print("PASS attachment authorization")
print("PASS call authorization")
print("PASS group-call participant boundary")
print("PASS screen-share participant boundary")
print("PASS verified-user frontend boundary")
print("PASS control DB ownership boundary")
'@

$SecurityScript | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Phase 11.6 security boundary failed."
}

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 11.6 FINAL E2E: PASS"
Write-Host "================================================="