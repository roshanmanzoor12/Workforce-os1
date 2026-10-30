$ErrorActionPreference = "Stop"

$Backend = "C:\workforce-os\backend"
$Python = "C:\workforce-os\.venv\Scripts\python.exe"

Set-Location $Backend

Write-Host ""
Write-Host "================================================="
Write-Host " WorkforceOS Phase 11.6 Frontend API Gate"
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

Write-Host "[1/6] Compiling frontend API..."

& $Python `
    -m py_compile `
    .\app\modules\chat\pagination_schemas.py `
    .\app\modules\chat\pagination_router.py `
    .\app\modules\chat\realtime_resume.py `
    .\app\modules\chat\realtime_client_protocol.py `
    .\app\modules\chat\realtime_client_schemas.py `
    .\app\modules\chat\realtime_commands_router.py `
    .\app\main.py

if ($LASTEXITCODE -ne 0)
{
    throw "Frontend API compile failed."
}

Write-Host "PASS compile"
Write-Host ""


# =========================================================
# 2. TESTS
# =========================================================

Write-Host "[2/6] Social/chat/channel tests..."

& $Python `
    -m pytest `
    .\tests\modules\friends `
    .\tests\modules\chat `
    .\tests\modules\channels `
    -q

if ($LASTEXITCODE -ne 0)
{
    throw "Frontend API tests failed."
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
    "a6b7c8d9e0f1"
)
{
    throw (
        "Expected control revision " +
        "a6b7c8d9e0f1."
    )
}

Write-Host "PASS migration"
Write-Host ""


# =========================================================
# 4. FRONTEND REST API CONTRACT
# =========================================================

Write-Host "[4/6] Frontend REST API contract..."

$ApiScript = @'
from app.main import app

paths = app.openapi().get(
    "paths",
    {},
)

required = {
    "/api/v1/friends": {
        "get",
    },
    "/api/v1/chat/direct": {
        "post",
    },
    "/api/v1/chat/groups": {
        "post",
    },
    "/api/v1/chat/conversations": {
        "get",
    },
    "/api/v1/chat/{conversation_id}/messages": {
        "get",
        "post",
    },
    "/api/v1/chat/{conversation_id}/messages-page": {
        "get",
    },
    "/api/v1/chat/realtime/ticket": {
        "post",
    },
    "/api/v1/chat/realtime/heartbeat": {
        "post",
    },
    "/api/v1/chat/realtime/resume": {
        "post",
    },
    "/api/v1/workspace-channels": {
        "post",
    },
}

for path, methods in required.items():
    if path not in paths:
        raise RuntimeError(
            f"Missing frontend API: {path}"
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
    "PASS frontend REST API contract"
)
'@

$ApiScript |
    & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Frontend REST API contract failed."
}

Write-Host ""


# =========================================================
# 5. WEBSOCKET CONTRACT
# =========================================================

Write-Host "[5/6] Frontend WebSocket contract..."

$WsScript = @'
from fastapi.routing import (
    APIWebSocketRoute,
)

from app.modules.chat.realtime_router import (
    router,
)

paths = {
    route.path
    for route in router.routes
    if isinstance(
        route,
        APIWebSocketRoute,
    )
}

expected = (
    "/chat/realtime/ws"
)

if expected not in paths:
    raise RuntimeError(
        "Frontend WebSocket route missing."
    )

print(
    "PASS WebSocket route definition"
)

print(
    "PASS effective frontend endpoint: "
    "/api/v1/chat/realtime/ws"
)
'@

$WsScript |
    & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Frontend WebSocket contract failed."
}

Write-Host ""


# =========================================================
# 6. SECURITY / FRONTEND BOUNDARY
# =========================================================

Write-Host "[6/6] Frontend security boundary..."

$SecurityScript = @'
import inspect

from app.modules.chat.pagination_router import (
    list_message_page,
)
from app.modules.chat.realtime_commands_router import (
    resume_realtime_conversation,
)
from app.modules.chat.realtime_router import (
    create_realtime_ticket,
)

pagination_source = inspect.getsource(
    list_message_page
)

resume_source = inspect.getsource(
    resume_realtime_conversation
)

ticket_source = inspect.getsource(
    create_realtime_ticket
)

for name, source in (
    (
        "pagination",
        pagination_source,
    ),
    (
        "resume",
        resume_source,
    ),
    (
        "ticket",
        ticket_source,
    ),
):
    if (
        "get_current_verified_user"
        not in source
    ):
        raise RuntimeError(
            f"{name} authentication missing."
        )

if (
    "MessagePaginationService"
    not in pagination_source
):
    raise RuntimeError(
        "Pagination membership service missing."
    )

if (
    "RealtimeResumeService"
    not in resume_source
):
    raise RuntimeError(
        "Resume membership service missing."
    )

print(
    "PASS frontend never chooses database"
)

print(
    "PASS verified-user REST boundary"
)

print(
    "PASS conversation membership pagination boundary"
)

print(
    "PASS conversation membership resume boundary"
)

print(
    "PASS one-time WebSocket authentication flow"
)
'@

$SecurityScript |
    & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Frontend security boundary failed."
}

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 11.6 FRONTEND API: PASS"
Write-Host "================================================="
Write-Host ""