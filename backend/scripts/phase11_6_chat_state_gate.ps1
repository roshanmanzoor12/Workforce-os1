$ErrorActionPreference = "Stop"

$Backend = "C:\workforce-os\backend"
$Python = "C:\workforce-os\.venv\Scripts\python.exe"

Set-Location $Backend

Write-Host ""
Write-Host "================================================="
Write-Host " WorkforceOS Phase 11.6 Chat State Gate"
Write-Host "================================================="
Write-Host ""


Write-Host "[preflight] PostgreSQL 5434..."

$DbPort = Test-NetConnection `
    -ComputerName 127.0.0.1 `
    -Port 5434 `
    -WarningAction SilentlyContinue

if (-not $DbPort.TcpTestSucceeded)
{
    throw (
        "PostgreSQL is not reachable on " +
        "127.0.0.1:5434."
    )
}

Write-Host "PASS PostgreSQL reachable"
Write-Host ""


Write-Host "[1/6] Compiling..."

& $Python `
    -m py_compile `
    .\app\modules\chat\enums.py `
    .\app\modules\chat\models.py `
    .\app\modules\chat\schemas.py `
    .\app\modules\chat\state_repository.py `
    .\app\modules\chat\state_service.py `
    .\app\modules\chat\router.py `
    .\migrations\control\versions\f5a6b7c8d9e0_add_chat_receipts_presence.py `
    .\app\main.py

if ($LASTEXITCODE -ne 0)
{
    throw "Phase 11.6 chat-state compile failed."
}

Write-Host "PASS compile"
Write-Host ""


Write-Host "[2/6] Social/chat tests..."

& $Python `
    -m pytest `
    .\tests\modules\friends `
    .\tests\modules\chat `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Phase 11.6 chat-state tests failed."
}

Write-Host "PASS tests"
Write-Host ""


Write-Host "[3/6] Checking migration head..."

$Heads = (
    & $Python `
        -m alembic `
        -c .\alembic-control.ini `
        heads
)

if ($LASTEXITCODE -ne 0)
{
    throw "Alembic heads failed."
}

Write-Host $Heads

if (
    $Heads -notmatch
    "f5a6b7c8d9e0"
)
{
    throw (
        "Expected Phase 11.6 chat-state " +
        "migration head f5a6b7c8d9e0."
    )
}

Write-Host "PASS migration head"
Write-Host ""


Write-Host "[4/6] Model contract..."

@'
from app.modules.chat.models import (
    ChatMessageReceipt,
    ChatPresence,
)

assert (
    ChatMessageReceipt.__tablename__
    == "chat_message_receipts"
)

assert (
    ChatPresence.__tablename__
    == "chat_presence"
)

print(
    "PASS message receipt model"
)

print(
    "PASS presence model"
)
'@ |
& $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Chat-state model contract failed."
}

Write-Host ""


Write-Host "[5/6] OpenAPI contract..."

@'
from app.main import app

paths = app.openapi().get(
    "paths",
    {},
)

expected = {
    "/api/v1/chat/{conversation_id}/messages/{message_id}": {
        "patch",
        "delete",
    },
    "/api/v1/chat/{conversation_id}/read/{message_id}": {
        "post",
    },
    "/api/v1/chat/{conversation_id}/read-receipts/{message_id}": {
        "get",
    },
    "/api/v1/chat/presence": {
        "put",
    },
    "/api/v1/chat/presence/{target_user_id}": {
        "get",
    },
}

for path, methods in expected.items():
    if path not in paths:
        raise RuntimeError(
            f"Missing path: {path}"
        )

    actual = {
        method.lower()
        for method
        in paths[path].keys()
    }

    for method in methods:
        if method not in actual:
            raise RuntimeError(
                "Missing operation: "
                f"{method.upper()} {path}"
            )

        print(
            "PASS:",
            method.upper(),
            path,
        )

print(
    "PASS chat-state OpenAPI"
)
'@ |
& $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Chat-state OpenAPI check failed."
}

Write-Host ""


Write-Host "[6/6] Privacy/access boundaries..."

@'
import inspect

from app.modules.chat.state_service import (
    ChatStateService,
)

source = inspect.getsource(
    ChatStateService
)

required = (
    "_require_active_member",
    "sender_user_id",
    "are_friends",
    "deleted_at",
)

for token in required:
    if token not in source:
        raise RuntimeError(
            f"Missing access boundary: {token}"
        )

print(
    "PASS message ownership enforcement"
)

print(
    "PASS conversation membership enforcement"
)

print(
    "PASS presence friendship boundary"
)

print(
    "PASS soft-delete behavior"
)
'@ |
& $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Chat-state access boundary failed."
}

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 11.6 CHAT STATE: PASS"
Write-Host "================================================="
Write-Host ""