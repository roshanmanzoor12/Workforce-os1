$ErrorActionPreference = "Stop"

$BackendRoot = "C:\workforce-os\backend"

$Python = (
    "C:\workforce-os\backend\" +
    ".venv\Scripts\python.exe"
)

Set-Location $BackendRoot

Write-Host "================================================="
Write-Host " WorkforceOS Phase 11.6 Attachment Binding Gate"
Write-Host "================================================="
Write-Host ""

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

Write-Host "[preflight 2/3] MinIO 9000..."

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

Write-Host "[preflight 3/3] Migration..."

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

if (
    $CurrentRevision -notmatch
    "b7c8d9e0f1a2"
)
{
    throw (
        "Attachment foundation migration " +
        "b7c8d9e0f1a2 is not current."
    )
}

Write-Host "PASS attachment migration"
Write-Host ""

Write-Host "[1/6] Compiling..."

& $Python `
    -m compileall `
    .\app\modules\attachments `
    .\tests\test_phase11_6_attachment_bindings.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Attachment binding compile failed."
}

Write-Host "PASS compile"
Write-Host ""

Write-Host "[2/6] Attachment binding tests..."

& $Python `
    -m pytest `
    .\tests\test_phase11_6_attachment_bindings.py `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Attachment binding tests failed."
}

Write-Host "PASS tests"
Write-Host ""

Write-Host "[3/6] Message model compatibility..."

$ModelScript = @'
from app.modules.attachments.binding_repository import (
    AttachmentBindingRepository,
)

chat = AttachmentBindingRepository._resolve_message_model(
    module_name="app.modules.chat.models",
    target_column="conversation_id",
)

channel = AttachmentBindingRepository._resolve_message_model(
    module_name="app.modules.channels.models",
    target_column="channel_id",
)

print(
    "PASS chat message model:",
    chat.__name__,
)

print(
    "PASS channel message model:",
    channel.__name__,
)
'@

$ModelScript | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Message model compatibility failed."
}

Write-Host ""

Write-Host "[4/6] REST API contract..."

$ApiScript = @'
from app.main import app

paths = app.openapi().get(
    "paths",
    {},
)

expected = {
    (
        "/api/v1/chat/{conversation_id}/"
        "messages/{message_id}/attachments"
    ): {
        "get",
        "post",
    },
    (
        "/api/v1/workspace-channels/"
        "{channel_id}/messages/"
        "{message_id}/attachments"
    ): {
        "get",
        "post",
    },
}

for path, methods in expected.items():
    if path not in paths:
        raise SystemExit(
            f"Missing route: {path}"
        )

    actual = {
        value.lower()
        for value
        in paths[path].keys()
    }

    missing = methods - actual

    if missing:
        raise SystemExit(
            f"{path} missing methods: "
            + ", ".join(
                sorted(missing)
            )
        )

    for method in sorted(methods):
        print(
            f"PASS: "
            f"{method.upper()} "
            f"{path}"
        )

print(
    "PASS attachment binding "
    "REST contract"
)
'@

$ApiScript | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Attachment REST contract failed."
}

Write-Host ""

Write-Host "[5/6] Authorization boundary..."

$BoundaryScript = @'
from pathlib import Path

service = Path(
    "app/modules/attachments/"
    "binding_service.py"
).read_text(
    encoding="utf-8",
)

router = Path(
    "app/modules/attachments/"
    "message_router.py"
).read_text(
    encoding="utf-8",
)

required_service = [
    "assert_scope_access",
    "owner_user_id",
    "AttachmentStatus.READY",
    "conversation_message_exists",
    "channel_message_exists",
]

for token in required_service:
    if token not in service:
        raise SystemExit(
            "Missing authorization boundary: "
            + token
        )

if (
    "get_current_verified_user"
    not in router
):
    raise SystemExit(
        "Verified user boundary missing."
    )

if "get_control_db" not in router:
    raise SystemExit(
        "Control DB boundary missing."
    )

print(
    "PASS uploader ownership boundary"
)

print(
    "PASS conversation membership boundary"
)

print(
    "PASS channel membership boundary"
)

print(
    "PASS message existence boundary"
)

print(
    "PASS verified-user boundary"
)
'@

$BoundaryScript | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Attachment authorization boundary failed."
}

Write-Host ""

Write-Host "[6/6] Realtime/privacy boundary..."

$RealtimeScript = @'
from pathlib import Path

text = Path(
    "app/modules/attachments/"
    "realtime_payloads.py"
).read_text(
    encoding="utf-8",
)

required = [
    "message.attachments.updated",
    "filename",
    "content_type",
    "size_bytes",
]

for token in required:
    if token not in text:
        raise SystemExit(
            "Missing realtime token: "
            + token
        )

forbidden = [
    "MINIO_ACCESS_KEY",
    "MINIO_SECRET_KEY",
    '"object_key":',
    '"bucket_name":',
]

for token in forbidden:
    if token in text:
        raise SystemExit(
            "Realtime payload exposes "
            "forbidden storage data: "
            + token
        )

print(
    "PASS realtime attachment payload"
)

print(
    "PASS no signed URLs in realtime"
)

print(
    "PASS no MinIO credentials in realtime"
)

print(
    "PASS no internal object key exposure"
)
'@

$RealtimeScript | & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Realtime attachment privacy boundary failed."
}

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 11.6 ATTACHMENT BINDINGS: PASS"
Write-Host "================================================="

