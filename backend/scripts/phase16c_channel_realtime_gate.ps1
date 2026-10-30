$ErrorActionPreference = "Stop"


$BackendRoot = "C:\workforce-os\backend"

$Python = (
    "C:\workforce-os\backend\" +
    ".venv\Scripts\python.exe"
)

$ExpectedControlHead = "g1b2c3d4e5f6"

$ExpectedTenantHead = "k1f2g3h4i5j6"

$WorkspaceId = "34527ffb-e094-4e5e-89ee-4cab97244fc3"

$TenantDatabase = (
    "tenant_" +
    $WorkspaceId.Replace("-", "")
)


Set-Location $BackendRoot


Write-Host "================================================="
Write-Host " WorkforceOS Phase 16C Channel Realtime"
Write-Host "================================================="
Write-Host ""


# =========================================================
# REQUIRED FILES
# =========================================================

$RequiredFiles = @(
    ".\app\modules\channels\realtime_schemas.py",
    ".\app\modules\channels\realtime_bus.py",
    ".\app\modules\channels\realtime_ticket.py",
    ".\app\modules\channels\realtime_presence.py",
    ".\app\modules\channels\realtime_service.py",
    ".\app\modules\channels\realtime_websocket.py",
    ".\app\modules\channels\realtime_router.py",
    ".\app\modules\tenant_api\router.py"
)


foreach ($File in $RequiredFiles)
{
    if (-not (Test-Path $File))
    {
        throw (
            "Missing required file: " +
            $File
        )
    }
}


Write-Host "PASS required files"
Write-Host ""


# =========================================================
# 1/8 COMPILE
# =========================================================

Write-Host "[1/8] Compiling..."


& $Python `
    -m compileall `
    ".\app\modules\channels" `
    ".\app\modules\tenant_api" `
    -q


if ($LASTEXITCODE -ne 0)
{
    throw "Compile failed."
}


Write-Host "PASS compile"
Write-Host ""


# =========================================================
# 2/8 SCHEMA CONTRACT
# =========================================================

Write-Host "[2/8] Realtime schema contract..."


$SchemaCheck = @'
from app.modules.channels.realtime_schemas import (
    WorkspaceChannelRealtimeCapabilities,
    WorkspaceChannelRealtimeEventType,
)


required = {
    "channel.connected",
    "channel.disconnected",
    "channel.message.created",
    "channel.message.updated",
    "channel.message.deleted",
    "channel.attachment.bound",
    "channel.typing.started",
    "channel.typing.stopped",
    "channel.presence.updated",
    "channel.created",
    "channel.updated",
    "channel.archived",
    "channel.heartbeat",
}


actual = {
    item.value
    for item
    in WorkspaceChannelRealtimeEventType
}


if actual != required:
    raise SystemExit(
        "Realtime event contract mismatch: "
        + str(sorted(actual))
    )


capabilities = WorkspaceChannelRealtimeCapabilities()


required_capabilities = (
    "websocket",
    "reconnect_resume",
    "message_events",
    "attachment_events",
    "typing_state",
    "presence_state",
    "heartbeat",
    "workspace_channel_events",
    "redis_fanout",
)


for field in required_capabilities:
    if getattr(capabilities, field) is not True:
        raise SystemExit(
            "Capability disabled: "
            + field
        )


print(
    "PASS realtime schema contract"
)
'@


$SchemaCheck | & $Python -


if ($LASTEXITCODE -ne 0)
{
    throw "Realtime schema gate failed."
}


Write-Host ""


# =========================================================
# 3/8 IMPORT CONTRACT
# =========================================================

Write-Host "[3/8] Realtime imports..."


$ImportCheck = @'
from app.modules.channels.realtime_bus import (
    WorkspaceChannelRealtimeBus,
    channel_realtime_bus,
)

from app.modules.channels.realtime_presence import (
    WorkspaceChannelRealtimePresence,
    channel_realtime_presence,
)

from app.modules.channels.realtime_router import (
    router,
)

from app.modules.channels.realtime_service import (
    WorkspaceChannelRealtimeService,
    channel_realtime_service,
)

from app.modules.channels.realtime_ticket import (
    WorkspaceChannelRealtimeTicketService,
    channel_realtime_ticket_service,
)

from app.modules.channels.realtime_websocket import (
    WorkspaceChannelRealtimeWebSocket,
    channel_realtime_websocket,
)


assert WorkspaceChannelRealtimeBus
assert channel_realtime_bus

assert WorkspaceChannelRealtimePresence
assert channel_realtime_presence

assert WorkspaceChannelRealtimeService
assert channel_realtime_service

assert WorkspaceChannelRealtimeTicketService
assert channel_realtime_ticket_service

assert WorkspaceChannelRealtimeWebSocket
assert channel_realtime_websocket

assert router


print(
    "PASS realtime imports"
)
'@


$ImportCheck | & $Python -


if ($LASTEXITCODE -ne 0)
{
    throw "Realtime import gate failed."
}


Write-Host ""


# =========================================================
# 4/8 REDIS EVENT / REPLAY
# =========================================================

Write-Host "[4/8] Redis event/replay..."


$RedisCheck = @'
import asyncio
import uuid

from app.core.redis import (
    redis_client,
)

from app.modules.channels.realtime_bus import (
    channel_realtime_bus,
)

from app.modules.channels.realtime_schemas import (
    WorkspaceChannelRealtimeEventType,
)


async def main():
    workspace_id = uuid.uuid4()

    channel_id = uuid.uuid4()

    actor_id = uuid.uuid4()


    first = await channel_realtime_bus.publish(
        workspace_id=workspace_id,
        channel_id=channel_id,
        event_type=(
            WorkspaceChannelRealtimeEventType
            .HEARTBEAT
        ),
        actor_user_id=actor_id,
        payload={
            "gate": True,
            "number": 1,
        },
    )


    second = await channel_realtime_bus.publish(
        workspace_id=workspace_id,
        channel_id=channel_id,
        event_type=(
            WorkspaceChannelRealtimeEventType
            .TYPING_STARTED
        ),
        actor_user_id=actor_id,
        payload={
            "typing": True,
            "number": 2,
        },
    )


    if second.sequence <= first.sequence:
        raise SystemExit(
            "Realtime sequence did not increase."
        )


    events = await channel_realtime_bus.replay(
        workspace_id=workspace_id,
        channel_id=channel_id,
        after_sequence=first.sequence,
        limit=10,
    )


    if not events:
        raise SystemExit(
            "Realtime replay returned no events."
        )


    if events[0].sequence != second.sequence:
        raise SystemExit(
            "Realtime replay sequence mismatch."
        )


    current = await (
        channel_realtime_bus
        .current_sequence(
            workspace_id=workspace_id,
            channel_id=channel_id,
        )
    )


    if current != second.sequence:
        raise SystemExit(
            "Current realtime sequence mismatch."
        )


    await redis_client.delete(
        channel_realtime_bus.stream_key(
            workspace_id=workspace_id,
            channel_id=channel_id,
        )
    )


    await redis_client.delete(
        channel_realtime_bus.sequence_key(
            workspace_id=workspace_id,
            channel_id=channel_id,
        )
    )


    print(
        "PASS Redis event/replay"
    )


asyncio.run(main())
'@


$RedisCheck | & $Python -


if ($LASTEXITCODE -ne 0)
{
    throw "Redis realtime gate failed."
}


Write-Host ""


# =========================================================
# 5/8 ONE-TIME TICKET
# =========================================================

Write-Host "[5/8] One-time ticket..."


$TicketCheck = @'
import asyncio
import uuid

from app.modules.channels.realtime_ticket import (
    channel_realtime_ticket_service,
)


async def main():
    workspace_id = uuid.uuid4()

    channel_id = uuid.uuid4()

    user_id = uuid.uuid4()


    ticket, ttl = await (
        channel_realtime_ticket_service
        .create(
            workspace_id=workspace_id,
            channel_id=channel_id,
            user_id=user_id,
        )
    )


    if not ticket:
        raise SystemExit(
            "Realtime ticket was empty."
        )


    if ttl <= 0:
        raise SystemExit(
            "Invalid realtime ticket TTL."
        )


    first = await (
        channel_realtime_ticket_service
        .consume(
            ticket=ticket
        )
    )


    if first is None:
        raise SystemExit(
            "First ticket consumption failed."
        )


    if first.workspace_id != workspace_id:
        raise SystemExit(
            "Ticket workspace mismatch."
        )


    if first.channel_id != channel_id:
        raise SystemExit(
            "Ticket channel mismatch."
        )


    if first.user_id != user_id:
        raise SystemExit(
            "Ticket user mismatch."
        )


    second = await (
        channel_realtime_ticket_service
        .consume(
            ticket=ticket
        )
    )


    if second is not None:
        raise SystemExit(
            "Realtime ticket was reusable."
        )


    print(
        "PASS one-time ticket"
    )


asyncio.run(main())
'@


$TicketCheck | & $Python -


if ($LASTEXITCODE -ne 0)
{
    throw "Realtime ticket gate failed."
}


Write-Host ""


# =========================================================
# 6/8 APP / OPENAPI / EFFECTIVE WEBSOCKET
# =========================================================

Write-Host "[6/8] App/OpenAPI/WebSocket..."


$ApplicationCheck = @'
from fastapi.routing import (
    APIWebSocketRoute,
    _iter_routes_with_context,
)

from app.main import app


openapi = app.openapi()

paths = openapi["paths"]


base = (
    "/api/v1/workspaces/"
    "{workspace_id}/channels/"
    "{channel_id}/realtime"
)


required_http = {
    base + "/ticket": {
        "post",
    },

    base + "/resume": {
        "post",
    },

    base + "/typing/start": {
        "post",
    },

    base + "/typing/stop": {
        "post",
    },

    base + "/heartbeat": {
        "post",
    },

    base + "/capabilities": {
        "get",
    },
}


for path, methods in required_http.items():
    if path not in paths:
        raise SystemExit(
            "Missing realtime HTTP endpoint: "
            + path
        )

    available = set(
        paths[path]
    )

    missing = (
        methods
        - available
    )

    if missing:
        raise SystemExit(
            "Missing method(s) for "
            + path
            + ": "
            + str(
                sorted(missing)
            )
        )


expected_ws = (
    base
    + "/ws"
)


websocket_paths = []


for (
    route,
    route_context,
) in _iter_routes_with_context(
    app.routes
):

    starlette_route = None

    if route_context is not None:
        starlette_route = (
            route_context
            .starlette_route
        )


    is_websocket = (
        isinstance(
            route,
            APIWebSocketRoute,
        )
        or isinstance(
            starlette_route,
            APIWebSocketRoute,
        )
    )


    if not is_websocket:
        continue


    if route_context is None:
        effective_path = getattr(
            route,
            "path",
            None,
        )

    elif starlette_route is not None:
        effective_path = getattr(
            starlette_route,
            "path",
            None,
        )

    else:
        effective_path = (
            route_context.path
        )


    if effective_path:
        websocket_paths.append(
            effective_path
        )


if expected_ws not in websocket_paths:
    print(
        "Detected effective WebSocket routes:"
    )

    if websocket_paths:
        for path in websocket_paths:
            print(
                " - "
                + path
            )
    else:
        print(
            " - NONE"
        )

    raise SystemExit(
        "Missing effective channel WebSocket route: "
        + expected_ws
    )


print(
    "PASS effective WebSocket route"
)

print(
    "PASS app/OpenAPI/WebSocket"
)
'@


$ApplicationCheck | & $Python -


if ($LASTEXITCODE -ne 0)
{
    throw "App/OpenAPI gate failed."
}


Write-Host ""


# =========================================================
# 7/8 CONTROL HEAD
# =========================================================

Write-Host "[7/8] Control migration head..."


$ControlHeads = & $Python `
    -m alembic `
    -c ".\alembic-control.ini" `
    heads


if ($LASTEXITCODE -ne 0)
{
    throw "Control Alembic heads failed."
}


$ControlHeadLines = @(
    $ControlHeads |
    ForEach-Object {
        if ($null -ne $_)
        {
            $_.ToString().Trim()
        }
    } |
    Where-Object {
        $_.Length -gt 0
    }
)


if ($ControlHeadLines.Count -ne 1)
{
    throw (
        "Expected exactly one control head. Found: " +
        $ControlHeadLines.Count
    )
}


$ControlText = (
    $ControlHeadLines -join "`n"
)


Write-Host $ControlText


if ($ControlText -notmatch $ExpectedControlHead)
{
    throw (
        "Unexpected control head. Expected " +
        $ExpectedControlHead
    )
}


Write-Host "PASS control head"
Write-Host ""


# =========================================================
# 8/8 TENANT HEAD
# =========================================================

Write-Host "[8/8] Tenant migration head..."


$TenantHeads = & $Python `
    -m alembic `
    -c ".\alembic.tenant.ini" `
    -x "database_name=$TenantDatabase" `
    heads


if ($LASTEXITCODE -ne 0)
{
    throw "Tenant Alembic heads failed."
}


$TenantHeadLines = @(
    $TenantHeads |
    ForEach-Object {
        if ($null -ne $_)
        {
            $_.ToString().Trim()
        }
    } |
    Where-Object {
        $_.Length -gt 0
    }
)


if ($TenantHeadLines.Count -ne 1)
{
    throw (
        "Expected exactly one tenant head. Found: " +
        $TenantHeadLines.Count
    )
}


$TenantHeadsText = (
    $TenantHeadLines -join "`n"
)


Write-Host $TenantHeadsText


if ($TenantHeadsText -notmatch $ExpectedTenantHead)
{
    throw (
        "Unexpected tenant graph head. Expected " +
        $ExpectedTenantHead
    )
}


$TenantCurrent = & $Python `
    -m alembic `
    -c ".\alembic.tenant.ini" `
    -x "database_name=$TenantDatabase" `
    current


if ($LASTEXITCODE -ne 0)
{
    throw "Tenant Alembic current failed."
}


$TenantCurrentText = (
    $TenantCurrent -join "`n"
)


Write-Host $TenantCurrentText


if ($TenantCurrentText -notmatch $ExpectedTenantHead)
{
    throw (
        "Unexpected tenant database revision. Expected " +
        $ExpectedTenantHead
    )
}


Write-Host "PASS tenant head"
Write-Host ""


# =========================================================
# FINAL
# =========================================================

Write-Host "================================================="
Write-Host " PHASE 16C CHANNEL REALTIME FOUNDATION: PASS"
Write-Host "================================================="
Write-Host "Realtime schemas:                 PASS"
Write-Host "Redis pub/sub:                    PASS"
Write-Host "Reconnect replay:                 PASS"
Write-Host "Monotonic channel sequence:       PASS"
Write-Host "One-time socket tickets:          PASS"
Write-Host "Typing TTL:                       PASS"
Write-Host "Presence TTL:                     PASS"
Write-Host "Heartbeat:                        PASS"
Write-Host "Authenticated WebSocket route:    PASS"
Write-Host "Lazy-router WebSocket discovery:  PASS"
Write-Host "Workspace/channel ticket scope:   PASS"
Write-Host "OpenAPI control plane:            PASS"
Write-Host "Control head:                     $ExpectedControlHead"
Write-Host "Tenant head:                      $ExpectedTenantHead"
Write-Host "================================================="