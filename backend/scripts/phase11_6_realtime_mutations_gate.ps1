$ErrorActionPreference = "Stop"

$Backend = "C:\workforce-os\backend"
$Python = "C:\workforce-os\.venv\Scripts\python.exe"

Set-Location $Backend

Write-Host ""
Write-Host "================================================="
Write-Host " WorkforceOS Phase 11.6 Realtime Mutation Gate"
Write-Host "================================================="
Write-Host ""


# =========================================================
# PREFLIGHT
# =========================================================

Write-Host "[preflight 1/2] PostgreSQL 5434..."

$DbPort = Test-NetConnection `
    -ComputerName 127.0.0.1 `
    -Port 5434 `
    -WarningAction SilentlyContinue

if (-not $DbPort.TcpTestSucceeded)
{
    throw "PostgreSQL 127.0.0.1:5434 unavailable."
}

Write-Host "PASS PostgreSQL reachable"
Write-Host ""


Write-Host "[preflight 2/2] Redis 6381..."

$RedisPort = Test-NetConnection `
    -ComputerName 127.0.0.1 `
    -Port 6381 `
    -WarningAction SilentlyContinue

if (-not $RedisPort.TcpTestSucceeded)
{
    throw "Redis 127.0.0.1:6381 unavailable."
}

Write-Host "PASS Redis reachable"
Write-Host ""


# =========================================================
# 1. COMPILE
# =========================================================

Write-Host "[1/6] Compiling..."

& $Python `
    -m py_compile `
    .\app\modules\chat\realtime_presence.py `
    .\app\modules\chat\realtime_publish_service.py `
    .\app\modules\chat\typing_command_service.py `
    .\app\modules\chat\realtime_command_schemas.py `
    .\app\modules\chat\realtime_commands_router.py `
    .\app\modules\chat\realtime_router.py `
    .\app\modules\chat\router.py `
    .\app\main.py

if ($LASTEXITCODE -ne 0)
{
    throw "Realtime mutation compile failed."
}

Write-Host "PASS compile"
Write-Host ""


# =========================================================
# 2. TESTS
# =========================================================

Write-Host "[2/6] Social/chat tests..."

& $Python `
    -m pytest `
    .\tests\modules\friends `
    .\tests\modules\chat `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Realtime mutation tests failed."
}

Write-Host "PASS tests"
Write-Host ""


# =========================================================
# 3. MIGRATION
# =========================================================

Write-Host "[3/6] Control migration..."

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
    "f5a6b7c8d9e0"
)
{
    throw (
        "Expected control revision " +
        "f5a6b7c8d9e0."
    )
}

Write-Host "PASS migration"
Write-Host ""


# =========================================================
# 4. API CONTRACT
# =========================================================

Write-Host "[4/6] Realtime command API..."

@'
from app.main import app

paths = app.openapi().get(
    "paths",
    {},
)

expected = {
    "/api/v1/chat/realtime/typing/{conversation_id}/start": {
        "post",
    },
    "/api/v1/chat/realtime/typing/{conversation_id}/stop": {
        "post",
    },
    "/api/v1/chat/realtime/typing/{conversation_id}": {
        "get",
    },
    "/api/v1/chat/realtime/heartbeat": {
        "post",
    },
}

for path, methods in expected.items():
    if path not in paths:
        raise RuntimeError(
            f"Missing path: {path}"
        )

    for method in methods:
        if method not in paths[path]:
            raise RuntimeError(
                f"Missing {method.upper()} {path}"
            )

        print(
            "PASS:",
            method.upper(),
            path,
        )

print(
    "PASS realtime command API"
)
'@ |
& $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Realtime command API contract failed."
}

Write-Host ""


# =========================================================
# 5. AUTOMATIC EVENT PUBLISHING
# =========================================================

Write-Host "[5/6] Automatic mutation publishing..."

@'
import inspect

from app.modules.chat.router import (
    delete_message,
    edit_message,
    mark_message_read,
    send_message,
)

contracts = (
    (
        send_message,
        "publisher.message_created(",
    ),
    (
        edit_message,
        "publisher.message_updated(",
    ),
    (
        delete_message,
        "publisher.message_deleted(",
    ),
    (
        mark_message_read,
        "publisher.message_read(",
    ),
)

for function, publish_token in contracts:
    source = inspect.getsource(
        function
    )

    commit_token = (
        "await session.commit()"
    )

    if commit_token not in source:
        raise RuntimeError(
            f"{function.__name__} commit missing."
        )

    if publish_token not in source:
        raise RuntimeError(
            f"{function.__name__} missing "
            f"{publish_token}"
        )

    commit_index = source.index(
        commit_token
    )

    publish_index = source.index(
        publish_token
    )

    if publish_index < commit_index:
        raise RuntimeError(
            f"{function.__name__} publishes "
            "before commit."
        )

    print(
        "PASS:",
        function.__name__,
        "commit-before-publish",
    )

print(
    "PASS automatic mutation publishing order"
)
'@ |
& $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Automatic event publishing check failed."
}

Write-Host ""


# =========================================================
# 6. SECURITY / REALTIME BOUNDARIES
# =========================================================

Write-Host "[6/6] Realtime boundaries..."

@'
import inspect

from app.modules.chat.realtime_commands_router import (
    realtime_heartbeat,
    start_typing,
)
from app.modules.chat.realtime_publish_service import (
    ChatRealtimePublishService,
)
from app.modules.chat.realtime_router import (
    chat_realtime_websocket,
)
from app.modules.chat.typing_command_service import (
    TypingCommandService,
)

typing_source = inspect.getsource(
    TypingCommandService
)

publisher_source = inspect.getsource(
    ChatRealtimePublishService
)

ws_source = inspect.getsource(
    chat_realtime_websocket
)

heartbeat_source = inspect.getsource(
    realtime_heartbeat
)

typing_route_source = inspect.getsource(
    start_typing
)

if "_require_active_member" not in typing_source:
    raise RuntimeError(
        "Typing membership gate missing."
    )

if "publish_best_effort" not in publisher_source:
    raise RuntimeError(
        "Best-effort publisher missing."
    )

if "connection_count" not in ws_source:
    raise RuntimeError(
        "Multi-device disconnect protection missing."
    )

if "mark_offline" not in ws_source:
    raise RuntimeError(
        "Automatic offline presence missing."
    )

if "get_current_verified_user" not in heartbeat_source:
    raise RuntimeError(
        "Heartbeat authentication missing."
    )

if "get_current_verified_user" not in typing_route_source:
    raise RuntimeError(
        "Typing authentication missing."
    )

print(
    "PASS typing membership enforcement"
)

print(
    "PASS authenticated typing commands"
)

print(
    "PASS authenticated heartbeat"
)

print(
    "PASS commit-before-realtime publish"
)

print(
    "PASS best-effort Redis publishing"
)

print(
    "PASS multi-device WebSocket presence"
)

print(
    "PASS automatic offline cleanup"
)
'@ |
& $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Realtime boundary check failed."
}

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 11.6 REALTIME MUTATIONS: PASS"
Write-Host "================================================="
Write-Host ""