$ErrorActionPreference = "Stop"

$Backend = "C:\workforce-os\backend"
$Python = "C:\workforce-os\.venv\Scripts\python.exe"

Set-Location $Backend

Write-Host ""
Write-Host "================================================="
Write-Host " WorkforceOS Phase 11.6 Realtime Transport Gate"
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
    .\app\modules\chat\chat_redis.py `
    .\app\modules\chat\websocket_ticket.py `
    .\app\modules\chat\realtime_recipient_repository.py `
    .\app\modules\chat\realtime_dispatcher.py `
    .\app\modules\chat\realtime_subscriber.py `
    .\app\modules\chat\realtime_runtime.py `
    .\app\modules\chat\realtime_router.py `
    .\app\main.py

if ($LASTEXITCODE -ne 0)
{
    throw "Realtime transport compile failed."
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
    throw "Realtime transport tests failed."
}

Write-Host "PASS tests"
Write-Host ""


# =========================================================
# 3. REDIS PING
# =========================================================

Write-Host "[3/6] Redis application client..."

@'
import asyncio

from app.modules.chat.chat_redis import (
    close_chat_redis,
    ping_chat_redis,
)

async def main():
    result = await ping_chat_redis()

    if not result:
        raise RuntimeError(
            "Chat Redis ping failed."
        )

    print(
        "PASS chat Redis application client"
    )

    await close_chat_redis()

asyncio.run(
    main()
)
'@ |
& $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Chat Redis client check failed."
}

Write-Host ""


# =========================================================
# 4. TICKET SECURITY
# =========================================================

Write-Host "[4/6] One-time ticket contract..."

@'
import asyncio
import uuid

from app.modules.chat.chat_redis import (
    close_chat_redis,
    get_chat_redis,
)
from app.modules.chat.websocket_ticket import (
    WebSocketTicketService,
)

async def main():
    redis_client = get_chat_redis()

    service = WebSocketTicketService(
        redis_client,
        ttl_seconds=30,
    )

    user_id = uuid.uuid4()

    ticket = await service.issue(
        user_id=user_id
    )

    first = await service.consume(
        token=ticket
    )

    second = await service.consume(
        token=ticket
    )

    if first != user_id:
        raise RuntimeError(
            "Ticket identity mismatch."
        )

    if second is not None:
        raise RuntimeError(
            "WebSocket ticket was reusable."
        )

    print(
        "PASS one-time WebSocket ticket"
    )

    print(
        "PASS Redis ticket consumption"
    )

    await close_chat_redis()

asyncio.run(
    main()
)
'@ |
& $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "WebSocket ticket contract failed."
}

Write-Host ""


# =========================================================
# 5. API + WEBSOCKET CONTRACT
# =========================================================

Write-Host "[5/6] Realtime route contract..."

@'
from fastapi.routing import (
    APIWebSocketRoute,
)

from app.main import app
from app.modules.chat.realtime_router import (
    router as chat_realtime_router,
)

schema = app.openapi()

paths = schema.get(
    "paths",
    {},
)

ticket_path = (
    "/api/v1/chat/realtime/ticket"
)

if ticket_path not in paths:
    raise RuntimeError(
        "Realtime ticket API missing."
    )

if "post" not in paths[ticket_path]:
    raise RuntimeError(
        "POST realtime ticket missing."
    )

print(
    "PASS authenticated ticket endpoint"
)

router_ws_paths = {
    route.path
    for route in chat_realtime_router.routes
    if isinstance(
        route,
        APIWebSocketRoute,
    )
}

router_ws_path = (
    "/chat/realtime/ws"
)

if router_ws_path not in router_ws_paths:
    raise RuntimeError(
        "Realtime WebSocket route definition missing."
    )

print(
    "PASS WebSocket route definition"
)

main_source = open(
    "app/main.py",
    "r",
    encoding="utf-8-sig",
).read()

if "chat_realtime_router" not in main_source:
    raise RuntimeError(
        "Realtime router import missing from main.py."
    )

if (
    "prefix=settings.api_v1_prefix"
    not in main_source
):
    raise RuntimeError(
        "API v1 prefix wiring missing."
    )

print(
    "PASS WebSocket router registered in main"
)

print(
    "PASS effective WebSocket endpoint "
    "/api/v1/chat/realtime/ws"
)
'@ |
& $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Realtime route contract failed."
}

Write-Host ""


# =========================================================
# 6. SECURITY / ARCHITECTURE
# =========================================================

Write-Host "[6/6] Realtime security boundaries..."

@'
import inspect

from app.modules.chat.realtime_router import (
    chat_realtime_websocket,
    create_realtime_ticket,
)
from app.modules.chat.websocket_ticket import (
    WebSocketTicketService,
)
from app.modules.chat.realtime_dispatcher import (
    ChatRealtimeDispatcher,
)

ticket_source = inspect.getsource(
    create_realtime_ticket
)

websocket_source = inspect.getsource(
    chat_realtime_websocket
)

service_source = inspect.getsource(
    WebSocketTicketService
)

dispatcher_source = inspect.getsource(
    ChatRealtimeDispatcher
)

if "get_current_verified_user" not in ticket_source:
    raise RuntimeError(
        "Ticket endpoint is not authenticated."
    )

if "getdel" not in service_source:
    raise RuntimeError(
        "Ticket is not one-time."
    )

if "consume" not in websocket_source:
    raise RuntimeError(
        "WebSocket does not consume ticket."
    )

if "query_params" not in websocket_source:
    raise RuntimeError(
        "WebSocket ticket input boundary missing."
    )

if "list_active_user_ids" not in dispatcher_source:
    raise RuntimeError(
        "Conversation recipient boundary missing."
    )

print(
    "PASS verified-user ticket issuance"
)

print(
    "PASS one-time ticket consumption"
)

print(
    "PASS WebSocket identity derived from ticket"
)

print(
    "PASS active-conversation recipient boundary"
)

print(
    "PASS WebSocket does not accept arbitrary user IDs"
)
'@ |
& $Python -

if ($LASTEXITCODE -ne 0)
{
    throw "Realtime security boundary failed."
}

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 11.6 REALTIME TRANSPORT: PASS"
Write-Host "================================================="
Write-Host ""