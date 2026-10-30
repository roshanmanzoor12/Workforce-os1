from __future__ import annotations

import uuid
from typing import (
    Annotated,
    Any,
)

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
)

from app.modules.channels.realtime_schemas import (
    WorkspaceChannelHeartbeatResponse,
    WorkspaceChannelRealtimeActionResponse,
    WorkspaceChannelRealtimeCapabilities,
    WorkspaceChannelRealtimeEventPage,
    WorkspaceChannelRealtimeResumeRequest,
    WorkspaceChannelRealtimeTicketResponse,
)
from app.modules.channels.realtime_service import (
    WorkspaceChannelRealtimeNotFoundError,
    WorkspaceChannelRealtimePermissionError,
    channel_realtime_service,
)
from app.modules.channels.realtime_websocket import (
    channel_realtime_websocket,
)
from app.modules.tenant_api.dependencies import (
    get_authorized_tenant_context,
)


router = APIRouter(
    prefix=(
        "/workspaces/"
        "{workspace_id}/channels/"
        "{channel_id}/realtime"
    ),
    tags=[
        "Workspace Channel Realtime",
    ],
)


TenantContext = Annotated[
    Any,
    Depends(
        get_authorized_tenant_context
    ),
]


def translate_error(
    exc: Exception,
) -> HTTPException:
    if isinstance(
        exc,
        WorkspaceChannelRealtimeNotFoundError,
    ):
        return HTTPException(
            status_code=404,
            detail=str(
                exc
            ),
        )

    if isinstance(
        exc,
        WorkspaceChannelRealtimePermissionError,
    ):
        return HTTPException(
            status_code=403,
            detail=str(
                exc
            ),
        )

    raise exc


# =========================================================
# TICKET
# =========================================================


@router.post(
    "/ticket",
    response_model=(
        WorkspaceChannelRealtimeTicketResponse
    ),
)
async def create_channel_realtime_ticket(
    workspace_id: uuid.UUID,
    channel_id: uuid.UUID,
    context: TenantContext,
) -> WorkspaceChannelRealtimeTicketResponse:
    try:
        return await (
            channel_realtime_service.ticket(
                workspace_id=workspace_id,
                channel_id=channel_id,
                context=context,
            )
        )

    except Exception as exc:
        raise translate_error(
            exc
        ) from exc


# =========================================================
# RESUME
# =========================================================


@router.post(
    "/resume",
    response_model=(
        WorkspaceChannelRealtimeEventPage
    ),
)
async def resume_channel_realtime(
    workspace_id: uuid.UUID,
    channel_id: uuid.UUID,
    payload:
        WorkspaceChannelRealtimeResumeRequest,
    context: TenantContext,
) -> WorkspaceChannelRealtimeEventPage:
    if (
        payload.channel_id
        != channel_id
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Payload channel_id "
                "does not match route."
            ),
        )

    try:
        return await (
            channel_realtime_service.resume(
                workspace_id=workspace_id,
                payload=payload,
                context=context,
            )
        )

    except Exception as exc:
        raise translate_error(
            exc
        ) from exc


# =========================================================
# TYPING
# =========================================================


@router.post(
    "/typing/start",
    response_model=(
        WorkspaceChannelRealtimeActionResponse
    ),
)
async def start_channel_typing(
    workspace_id: uuid.UUID,
    channel_id: uuid.UUID,
    context: TenantContext,
) -> WorkspaceChannelRealtimeActionResponse:
    try:
        return await (
            channel_realtime_service
            .start_typing(
                workspace_id=workspace_id,
                channel_id=channel_id,
                context=context,
            )
        )

    except Exception as exc:
        raise translate_error(
            exc
        ) from exc


@router.post(
    "/typing/stop",
    response_model=(
        WorkspaceChannelRealtimeActionResponse
    ),
)
async def stop_channel_typing(
    workspace_id: uuid.UUID,
    channel_id: uuid.UUID,
    context: TenantContext,
) -> WorkspaceChannelRealtimeActionResponse:
    try:
        return await (
            channel_realtime_service
            .stop_typing(
                workspace_id=workspace_id,
                channel_id=channel_id,
                context=context,
            )
        )

    except Exception as exc:
        raise translate_error(
            exc
        ) from exc


# =========================================================
# HEARTBEAT
# =========================================================


@router.post(
    "/heartbeat",
    response_model=(
        WorkspaceChannelHeartbeatResponse
    ),
)
async def channel_realtime_heartbeat(
    workspace_id: uuid.UUID,
    channel_id: uuid.UUID,
    context: TenantContext,
) -> WorkspaceChannelHeartbeatResponse:
    try:
        return await (
            channel_realtime_service
            .heartbeat(
                workspace_id=workspace_id,
                channel_id=channel_id,
                context=context,
            )
        )

    except Exception as exc:
        raise translate_error(
            exc
        ) from exc


# =========================================================
# CAPABILITIES
# =========================================================


@router.get(
    "/capabilities",
    response_model=(
        WorkspaceChannelRealtimeCapabilities
    ),
)
async def channel_realtime_capabilities(
    workspace_id: uuid.UUID,
    channel_id: uuid.UUID,
    context: TenantContext,
) -> WorkspaceChannelRealtimeCapabilities:
    try:
        await (
            channel_realtime_service
            .resolve_access(
                workspace_id=workspace_id,
                context=context,
            )
        )

        await (
            channel_realtime_service
            .require_channel(
                workspace_id=workspace_id,
                channel_id=channel_id,
                context=context,
            )
        )

        return (
            channel_realtime_service
            .capabilities()
        )

    except Exception as exc:
        raise translate_error(
            exc
        ) from exc


# =========================================================
# WEBSOCKET
# =========================================================


@router.websocket(
    "/ws"
)
async def workspace_channel_realtime_socket(
    websocket: WebSocket,
    workspace_id: uuid.UUID,
    channel_id: uuid.UUID,
    ticket: Annotated[
        str,
        Query(
            min_length=20,
            max_length=512,
        ),
    ],
) -> None:
    """
    Browser flow:

        POST .../realtime/ticket
            ->
        wss://host/api/v1/.../realtime/ws?ticket=...

    The ticket itself contains the authoritative workspace,
    channel and user identity.

    Route identifiers must match that ticket.
    """

    identity = await (
        __consume_and_validate_ticket(
            websocket=websocket,
            ticket=ticket,
            workspace_id=workspace_id,
            channel_id=channel_id,
        )
    )

    if identity is None:
        return

    
   # Ticket was validated but realtime_websocket.connect()
   # normally consumes tickets itself.

   # To preserve one-time semantics without issuing another
   # credential, delegate to its authenticated identity path.
    

    await (
        channel_realtime_websocket
        ._run(
            websocket=websocket,
            identity=identity,
        )
    )


async def __consume_and_validate_ticket(
    *,
    websocket: WebSocket,
    ticket: str,
    workspace_id: uuid.UUID,
    channel_id: uuid.UUID,
):
    from app.modules.channels.realtime_ticket import (
        channel_realtime_ticket_service,
    )

    identity = await (
        channel_realtime_ticket_service
        .consume(
            ticket=ticket
        )
    )

    if identity is None:
        await websocket.close(
            code=4401,
            reason=(
                "Invalid or expired "
                "realtime ticket."
            ),
        )

        return None

    if (
        identity.workspace_id
        != workspace_id
        or identity.channel_id
        != channel_id
    ):
        await websocket.close(
            code=4403,
            reason=(
                "Realtime ticket route "
                "does not match."
            ),
        )

        return None

    await websocket.accept()

    return identity


__all__ = [
    "router",
]