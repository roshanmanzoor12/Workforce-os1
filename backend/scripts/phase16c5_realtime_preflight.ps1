$ErrorActionPreference = "Stop"


$Root = (
    "C:\workforce-os\backend"
)

$Python = (
    "C:\workforce-os\backend\" +
    ".venv\Scripts\python.exe"
)


Set-Location $Root


Write-Host "================================================="
Write-Host " WorkforceOS Phase 16C.5 Realtime Preflight"
Write-Host "================================================="
Write-Host ""


Write-Host "[1/4] Channel imports..."


$ImportCode = @'
from app.modules.channels.realtime_router import router
from app.modules.channels.realtime_service import ChannelRealtimeService
from app.modules.channels.realtime_events import channel_realtime_events
from app.modules.channels.read_state_router import router as read_state_router

assert router
assert ChannelRealtimeService
assert channel_realtime_events
assert read_state_router

print("PASS channel imports")
'@


$ImportCode |
    & $Python -


if (
    $LASTEXITCODE
    -ne 0
)
{
    throw (
        "Channel import preflight failed."
    )
}


Write-Host ""


Write-Host "[2/4] Effective WebSocket route..."


$WebSocketCheck = @'
from fastapi.routing import _iter_routes_with_context
from starlette.routing import WebSocketRoute

from app.main import app


paths = []


for route, context in _iter_routes_with_context(
    app.routes
):
    candidate = None

    if context is not None:
        candidate = getattr(
            context,
            "starlette_route",
            None,
        )

    effective = (
        candidate
        or route
    )

    if isinstance(
        effective,
        WebSocketRoute,
    ):
        paths.append(
            effective.path
        )


expected = (
    "/api/v1/workspaces/"
    "{workspace_id}/channels/"
    "{channel_id}/realtime/ws"
)


if expected not in paths:
    raise SystemExit(
        "Missing effective channel websocket route. "
        + repr(paths)
    )


print(
    "PASS websocket route:",
    expected,
)
'@


$WebSocketCheck |
    & $Python -


if (
    $LASTEXITCODE
    -ne 0
)
{
    throw (
        "WebSocket preflight failed."
    )
}


Write-Host ""


Write-Host "[3/4] Read-state OpenAPI..."


$OpenApiCheck = @'
from app.main import app


paths = app.openapi()["paths"]


required = [
    (
        "/api/v1/workspace-channels/"
        "{channel_id}/read-state"
    ),
    (
        "/api/v1/workspace-channels/"
        "{channel_id}/read-all"
    ),
]


for path in required:
    if path not in paths:
        raise SystemExit(
            "Missing path: "
            + path
        )


print("PASS read-state OpenAPI")
'@


$OpenApiCheck |
    & $Python -


if (
    $LASTEXITCODE
    -ne 0
)
{
    throw (
        "Read-state OpenAPI failed."
    )
}


Write-Host ""


Write-Host "[4/4] Attachment channel route..."


$AttachmentCheck = @'
from app.main import app


path = (
    "/api/v1/workspace-channels/"
    "{channel_id}/messages/"
    "{message_id}/attachments"
)


paths = app.openapi()["paths"]


if path not in paths:
    raise SystemExit(
        "Missing channel attachment binding route."
    )


methods = set(
    paths[path]
)


if "post" not in methods:
    raise SystemExit(
        "Channel attachment POST binding missing."
    )


if "get" not in methods:
    raise SystemExit(
        "Channel attachment GET listing missing."
    )


print("PASS attachment channel route")
'@


$AttachmentCheck |
    & $Python -


if (
    $LASTEXITCODE
    -ne 0
)
{
    throw (
        "Attachment route preflight failed."
    )
}


Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 16C.5 REALTIME PREFLIGHT: PASS"
Write-Host "================================================="
Write-Host "Imports:                       PASS"
Write-Host "Effective WebSocket route:     PASS"
Write-Host "Durable read-state routes:     PASS"
Write-Host "Attachment binding route:      PASS"
Write-Host "================================================="