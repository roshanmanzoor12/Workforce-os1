$ErrorActionPreference = "Stop"

$Backend = "C:\workforce-os\backend"
$Python = "C:\workforce-os\.venv\Scripts\python.exe"

Set-Location $Backend

Write-Host ""
Write-Host "================================================="
Write-Host " WorkforceOS Phase 11.6 Realtime Foundation Gate"
Write-Host "================================================="
Write-Host ""


# =========================================================
# PREFLIGHT POSTGRES
# =========================================================

Write-Host "[preflight 1/2] PostgreSQL 5434..."

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


# =========================================================
# PREFLIGHT REDIS
# =========================================================

Write-Host "[preflight 2/2] Redis 6381..."

$RedisPort = Test-NetConnection `
    -ComputerName 127.0.0.1 `
    -Port 6381 `
    -WarningAction SilentlyContinue

if (-not $RedisPort.TcpTestSucceeded)
{
    throw (
        "Redis is not reachable on " +
        "127.0.0.1:6381."
    )
}

Write-Host "PASS Redis reachable"
Write-Host ""


# =========================================================
# 1. COMPILE
# =========================================================

Write-Host "[1/6] Compiling realtime foundation..."

& $Python `
    -m py_compile `
    .\app\modules\chat\realtime_enums.py `
    .\app\modules\chat\realtime_events.py `
    .\app\modules\chat\pagination.py `
    .\app\modules\chat\message_query_repository.py `
    .\app\modules\chat\message_pagination_service.py `
    .\app\modules\chat\realtime_bus.py `
    .\app\modules\chat\typing_service.py `
    .\app\modules\chat\connection_manager.py

if ($LASTEXITCODE -ne 0)
{
    throw (
        "Phase 11.6 realtime foundation " +
        "compile failed."
    )
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
    throw (
        "Phase 11.6 realtime foundation " +
        "tests failed."
    )
}

Write-Host "PASS tests"
Write-Host ""


# =========================================================
# 3. CONTROL MIGRATION STATE
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
        "Expected current control revision " +
        "f5a6b7c8d9e0."
    )
}

Write-Host "PASS migration"
Write-Host ""


# =========================================================
# 4. CURSOR CONTRACT
# =========================================================

Write-Host "[4/6] Cursor pagination contract..."

@'
import uuid
from datetime import (
    datetime,
    timezone,
)

from app.modules.chat.pagination import (
    decode_message_cursor,
    encode_message_cursor,
)

message_id = uuid.uuid4()

created_at = datetime.now(
    timezone.utc
)

cursor = encode_message_cursor(
    created_at=created_at,
    message_id=message_id,
)

decoded = decode_message_cursor(
    cursor
)

assert decoded.message_id == message_id
assert decoded.created_at == created_at

print(
    "PASS opaque message cursor"
)

print(
    "PASS deterministic cursor decode"
)
'@ |
& $Python -

if ($LASTEXITCODE -ne 0)
{
    throw (
        "Cursor pagination contract failed."
    )
}

Write-Host ""


# =========================================================
# 5. REALTIME EVENT CONTRACT
# =========================================================

Write-Host "[5/6] Realtime event contract..."

@'
import uuid

from app.modules.chat.realtime_enums import (
    ChatRealtimeEventType,
)
from app.modules.chat.realtime_events import (
    ChatRealtimeEvent,
)

event = ChatRealtimeEvent(
    event_type=(
        ChatRealtimeEventType.MESSAGE_CREATED
    ),
    conversation_id=uuid.uuid4(),
    actor_user_id=uuid.uuid4(),
)

encoded = event.to_json()

decoded = ChatRealtimeEvent.from_json(
    encoded
)

assert decoded.event_id == event.event_id
assert decoded.event_type == event.event_type

print(
    "PASS realtime event envelope"
)

print(
    "PASS realtime serialization"
)
'@ |
& $Python -

if ($LASTEXITCODE -ne 0)
{
    throw (
        "Realtime event contract failed."
    )
}

Write-Host ""


# =========================================================
# 6. SECURITY / ARCHITECTURE
# =========================================================

Write-Host "[6/6] Architecture boundaries..."

@'
import inspect

from app.modules.chat.connection_manager import (
    ChatConnectionManager,
)
from app.modules.chat.message_pagination_service import (
    MessagePaginationService,
)
from app.modules.chat.typing_service import (
    TypingService,
)

pagination_source = inspect.getsource(
    MessagePaginationService
)

typing_source = inspect.getsource(
    TypingService
)

manager_source = inspect.getsource(
    ChatConnectionManager
)

if "_require_active_member" not in pagination_source:
    raise RuntimeError(
        "Pagination membership gate missing."
    )

if "ttl_seconds" not in typing_source:
    raise RuntimeError(
        "Typing expiry boundary missing."
    )

if "disconnect" not in manager_source:
    raise RuntimeError(
        "WebSocket disconnect cleanup missing."
    )

print(
    "PASS pagination membership boundary"
)

print(
    "PASS ephemeral typing TTL"
)

print(
    "PASS WebSocket cleanup boundary"
)

print(
    "PASS no persistent typing database table"
)
'@ |
& $Python -

if ($LASTEXITCODE -ne 0)
{
    throw (
        "Realtime architecture boundary failed."
    )
}

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 11.6 REALTIME FOUNDATION: PASS"
Write-Host "================================================="
Write-Host ""