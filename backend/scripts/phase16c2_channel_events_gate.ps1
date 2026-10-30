$ErrorActionPreference = "Stop"


$BackendRoot = "C:\workforce-os\backend"

$Python = (
    "C:\workforce-os\backend\" +
    ".venv\Scripts\python.exe"
)


Set-Location $BackendRoot


Write-Host "================================================="
Write-Host " WorkforceOS Phase 16C.2 Channel Events"
Write-Host "================================================="
Write-Host ""


$RequiredFiles = @(
    ".\app\modules\channels\realtime_events.py",
    ".\app\modules\channels\realtime_attachment_bridge.py",
    ".\app\modules\channels\repository.py",
    ".\app\modules\channels\schemas.py",
    ".\app\modules\channels\service.py",
    ".\app\modules\channels\router.py"
)


foreach ($File in $RequiredFiles)
{
    if (-not (Test-Path $File))
    {
        throw (
            "Missing file: " +
            $File
        )
    }
}


Write-Host "[1/5] Compile..."


& $Python `
    -m compileall `
    ".\app\modules\channels" `
    -q


if ($LASTEXITCODE -ne 0)
{
    throw "Compile failed."
}


Write-Host "PASS compile"
Write-Host ""


Write-Host "[2/5] Imports..."


$ImportCheck = @'
from app.modules.channels.realtime_attachment_bridge import (
    WorkspaceChannelRealtimeAttachmentBridge,
    channel_realtime_attachment_bridge,
)
from app.modules.channels.realtime_events import (
    WorkspaceChannelRealtimeEventPublisher,
    channel_realtime_events,
)
from app.modules.channels.repository import (
    WorkspaceChannelRepository,
)
from app.modules.channels.schemas import (
    WorkspaceChannelMessageUpdateRequest,
)
from app.modules.channels.service import (
    WorkspaceChannelService,
)


assert WorkspaceChannelRealtimeAttachmentBridge
assert channel_realtime_attachment_bridge
assert WorkspaceChannelRealtimeEventPublisher
assert channel_realtime_events
assert WorkspaceChannelRepository
assert WorkspaceChannelMessageUpdateRequest
assert WorkspaceChannelService

print("PASS imports")
'@


$ImportCheck | & $Python -


if ($LASTEXITCODE -ne 0)
{
    throw "Import gate failed."
}


Write-Host ""


Write-Host "[3/5] OpenAPI mutations..."


$OpenApiCheck = @'
from app.main import app


paths = app.openapi()["paths"]

base = (
    "/api/v1/workspace-channels/"
    "{channel_id}/messages"
)

item = (
    base
    + "/{message_id}"
)

attachments = (
    item
    + "/attachments"
)


if "post" not in paths.get(base, {}):
    raise SystemExit(
        "Missing channel message POST."
    )


if "get" not in paths.get(base, {}):
    raise SystemExit(
        "Missing channel message GET."
    )


if "patch" not in paths.get(item, {}):
    raise SystemExit(
        "Missing channel message PATCH."
    )


if "delete" not in paths.get(item, {}):
    raise SystemExit(
        "Missing channel message DELETE."
    )


if "post" not in paths.get(
    attachments,
    {},
):
    raise SystemExit(
        "Missing channel attachment bind POST."
    )


if "get" not in paths.get(
    attachments,
    {},
):
    raise SystemExit(
        "Missing channel attachment GET."
    )


print("PASS OpenAPI mutations")
'@


$OpenApiCheck | & $Python -


if ($LASTEXITCODE -ne 0)
{
    throw "OpenAPI gate failed."
}


Write-Host ""


Write-Host "[4/5] Realtime event contract..."


$EventCheck = @'
from app.modules.channels.realtime_schemas import (
    WorkspaceChannelRealtimeEventType,
)


required = {
    "channel.created",
    "channel.updated",
    "channel.archived",
    "channel.message.created",
    "channel.message.updated",
    "channel.message.deleted",
    "channel.attachment.bound",
}


actual = {
    item.value
    for item
    in WorkspaceChannelRealtimeEventType
}


missing = required - actual


if missing:
    raise SystemExit(
        "Missing event types: "
        + str(sorted(missing))
    )


print("PASS realtime event contract")
'@


$EventCheck | & $Python -


if ($LASTEXITCODE -ne 0)
{
    throw "Realtime event gate failed."
}


Write-Host ""


Write-Host "[5/5] Effective WebSocket route..."


$WebSocketCheck = @'
from fastapi.routing import (
    APIWebSocketRoute,
    _iter_routes_with_context,
)
from app.main import app


expected = (
    "/api/v1/workspaces/"
    "{workspace_id}/channels/"
    "{channel_id}/realtime/ws"
)


paths = []


for route, context in (
    _iter_routes_with_context(
        app.routes
    )
):
    starlette_route = (
        context.starlette_route
        if context is not None
        else None
    )

    if not (
        isinstance(
            route,
            APIWebSocketRoute,
        )
        or isinstance(
            starlette_route,
            APIWebSocketRoute,
        )
    ):
        continue

    if context is None:
        path = getattr(
            route,
            "path",
            None,
        )
    elif starlette_route is not None:
        path = getattr(
            starlette_route,
            "path",
            None,
        )
    else:
        path = context.path

    if path:
        paths.append(path)


if expected not in paths:
    raise SystemExit(
        "Missing effective channel WebSocket route."
    )


print("PASS effective WebSocket route")
'@


$WebSocketCheck | & $Python -


if ($LASTEXITCODE -ne 0)
{
    throw "WebSocket route gate failed."
}


Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 16C.2 CHANNEL EVENTS FOUNDATION: PASS"
Write-Host "================================================="