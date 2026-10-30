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
    status,
)

from app.core.exceptions import ValidationError
from app.modules.tenant_api.dependencies import (
    get_authorized_tenant_context,
)
from app.modules.voice_channels.access import (
    resolve_voice_channel_access,
)
from app.modules.voice_channels.schemas import (
    VoiceBanResponse,
    VoiceCallPublic,
    VoiceCapabilitiesResponse,
    VoiceJoinResponse,
    VoiceModerationReasonRequest,
    VoiceModeratorStateRequest,
    VoiceParticipantListResponse,
    VoiceParticipantPublic,
    VoicePresenceHeartbeatRequest,
    VoiceRealtimeStateResponse,
    VoiceScreenShareResponse,
    VoiceSelfStateRequest,
    VoiceSignalPollResponse,
    VoiceSignalRequest,
    VoiceSignalResponse,
    VoiceSpeakingRequest,
)
from app.modules.voice_channels.service import (
    VoiceChannelNotFoundError,
    VoiceChannelPermissionError,
    VoiceChannelService,
)


router = APIRouter(
    prefix=(
        "/workspaces/"
        "{workspace_id}/channels/"
        "{channel_id}/voice"
    ),
    tags=[
        "voice-channels",
    ],
)


TenantContext = Annotated[
    Any,
    Depends(
        get_authorized_tenant_context
    ),
]


async def _access(
    *,
    workspace_id: uuid.UUID,
    context: Any,
):
    try:
        return await (
            resolve_voice_channel_access(
                workspace_id=workspace_id,
                context=context,
            )
        )

    except ValidationError as exc:
        raise HTTPException(
            status_code=403,
            detail=str(
                exc
            ),
        ) from exc


def _service(
    *,
    workspace_id: uuid.UUID,
    context: Any,
) -> VoiceChannelService:
    return VoiceChannelService(
        tenant_session=(
            context.tenant_session
        ),

        control_session=(
            context.control_session
        ),

        workspace_id=workspace_id,
    )


def _translate(
    exc: Exception,
) -> HTTPException:
    if isinstance(
        exc,
        VoiceChannelNotFoundError,
    ):
        return HTTPException(
            status_code=404,
            detail=str(
                exc
            ),
        )

    if isinstance(
        exc,
        VoiceChannelPermissionError,
    ):
        return HTTPException(
            status_code=403,
            detail=str(
                exc
            ),
        )

    if isinstance(
        exc,
        ValidationError,
    ):
        return HTTPException(
            status_code=422,
            detail=str(
                exc
            ),
        )

    raise exc


@router.get(
    "/active-call",
    response_model=VoiceCallPublic,
)
async def get_active_voice_call(
    workspace_id: uuid.UUID,
    channel_id: uuid.UUID,
    context: TenantContext,
) -> VoiceCallPublic:
    access = await _access(
        workspace_id=workspace_id,
        context=context,
    )

    try:
        return await (
            _service(
                workspace_id=workspace_id,
                context=context,
            )
            .active_call(
                access=access,
                channel_id=channel_id,
            )
        )

    except Exception as exc:
        raise _translate(
            exc
        ) from exc


@router.post(
    "/join",
    response_model=VoiceJoinResponse,
)
async def join_voice_channel(
    workspace_id: uuid.UUID,
    channel_id: uuid.UUID,
    context: TenantContext,
) -> VoiceJoinResponse:
    access = await _access(
        workspace_id=workspace_id,
        context=context,
    )

    try:
        return await (
            _service(
                workspace_id=workspace_id,
                context=context,
            )
            .join(
                access=access,
                channel_id=channel_id,
            )
        )

    except Exception as exc:
        raise _translate(
            exc
        ) from exc


@router.post(
    "/leave",
    response_model=VoiceParticipantPublic,
)
async def leave_voice_channel(
    workspace_id: uuid.UUID,
    channel_id: uuid.UUID,
    context: TenantContext,
) -> VoiceParticipantPublic:
    access = await _access(
        workspace_id=workspace_id,
        context=context,
    )

    try:
        return await (
            _service(
                workspace_id=workspace_id,
                context=context,
            )
            .leave(
                access=access,
                channel_id=channel_id,
            )
        )

    except Exception as exc:
        raise _translate(
            exc
        ) from exc


@router.get(
    "/participants",
    response_model=(
        VoiceParticipantListResponse
    ),
)
async def list_voice_participants(
    workspace_id: uuid.UUID,
    channel_id: uuid.UUID,
    context: TenantContext,
) -> VoiceParticipantListResponse:
    await _access(
        workspace_id=workspace_id,
        context=context,
    )

    try:
        return await (
            _service(
                workspace_id=workspace_id,
                context=context,
            )
            .participants(
                channel_id=channel_id
            )
        )

    except Exception as exc:
        raise _translate(
            exc
        ) from exc


@router.patch(
    "/me",
    response_model=VoiceParticipantPublic,
)
async def update_self_voice_state(
    workspace_id: uuid.UUID,
    channel_id: uuid.UUID,
    payload: VoiceSelfStateRequest,
    context: TenantContext,
) -> VoiceParticipantPublic:
    access = await _access(
        workspace_id=workspace_id,
        context=context,
    )

    try:
        return await (
            _service(
                workspace_id=workspace_id,
                context=context,
            )
            .self_state(
                access=access,
                channel_id=channel_id,
                payload=payload,
            )
        )

    except Exception as exc:
        raise _translate(
            exc
        ) from exc


@router.patch(
    "/participants/{user_id}/moderation",
    response_model=VoiceParticipantPublic,
)
async def moderate_voice_participant(
    workspace_id: uuid.UUID,
    channel_id: uuid.UUID,
    user_id: uuid.UUID,
    payload: VoiceModeratorStateRequest,
    context: TenantContext,
) -> VoiceParticipantPublic:
    access = await _access(
        workspace_id=workspace_id,
        context=context,
    )

    try:
        return await (
            _service(
                workspace_id=workspace_id,
                context=context,
            )
            .moderator_state(
                access=access,
                channel_id=channel_id,
                user_id=user_id,
                payload=payload,
            )
        )

    except Exception as exc:
        raise _translate(
            exc
        ) from exc


@router.post(
    "/participants/{user_id}/kick",
    response_model=VoiceParticipantPublic,
)
async def kick_voice_participant(
    workspace_id: uuid.UUID,
    channel_id: uuid.UUID,
    user_id: uuid.UUID,
    context: TenantContext,
) -> VoiceParticipantPublic:
    access = await _access(
        workspace_id=workspace_id,
        context=context,
    )

    try:
        return await (
            _service(
                workspace_id=workspace_id,
                context=context,
            )
            .kick(
                access=access,
                channel_id=channel_id,
                user_id=user_id,
            )
        )

    except Exception as exc:
        raise _translate(
            exc
        ) from exc


@router.post(
    "/bans/{user_id}",
    response_model=VoiceBanResponse,
)
async def ban_voice_user(
    workspace_id: uuid.UUID,
    channel_id: uuid.UUID,
    user_id: uuid.UUID,
    payload: VoiceModerationReasonRequest,
    context: TenantContext,
) -> VoiceBanResponse:
    access = await _access(
        workspace_id=workspace_id,
        context=context,
    )

    try:
        return await (
            _service(
                workspace_id=workspace_id,
                context=context,
            )
            .ban(
                access=access,
                channel_id=channel_id,
                user_id=user_id,
                reason=payload.reason,
            )
        )

    except Exception as exc:
        raise _translate(
            exc
        ) from exc


@router.delete(
    "/bans/{user_id}",
    response_model=VoiceBanResponse,
)
async def unban_voice_user(
    workspace_id: uuid.UUID,
    channel_id: uuid.UUID,
    user_id: uuid.UUID,
    context: TenantContext,
) -> VoiceBanResponse:
    access = await _access(
        workspace_id=workspace_id,
        context=context,
    )

    try:
        return await (
            _service(
                workspace_id=workspace_id,
                context=context,
            )
            .unban(
                access=access,
                channel_id=channel_id,
                user_id=user_id,
            )
        )

    except Exception as exc:
        raise _translate(
            exc
        ) from exc


@router.post(
    "/screen-share/start",
    response_model=VoiceScreenShareResponse,
)
async def start_voice_screen_share(
    workspace_id: uuid.UUID,
    channel_id: uuid.UUID,
    context: TenantContext,
) -> VoiceScreenShareResponse:
    access = await _access(
        workspace_id=workspace_id,
        context=context,
    )

    try:
        return await (
            _service(
                workspace_id=workspace_id,
                context=context,
            )
            .screen_share(
                access=access,
                channel_id=channel_id,
                enabled=True,
            )
        )

    except Exception as exc:
        raise _translate(
            exc
        ) from exc


@router.post(
    "/screen-share/stop",
    response_model=VoiceScreenShareResponse,
)
async def stop_voice_screen_share(
    workspace_id: uuid.UUID,
    channel_id: uuid.UUID,
    context: TenantContext,
) -> VoiceScreenShareResponse:
    access = await _access(
        workspace_id=workspace_id,
        context=context,
    )

    try:
        return await (
            _service(
                workspace_id=workspace_id,
                context=context,
            )
            .screen_share(
                access=access,
                channel_id=channel_id,
                enabled=False,
            )
        )

    except Exception as exc:
        raise _translate(
            exc
        ) from exc


@router.post(
    "/signal",
    response_model=VoiceSignalResponse,
)
async def send_voice_signal(
    workspace_id: uuid.UUID,
    channel_id: uuid.UUID,
    payload: VoiceSignalRequest,
    context: TenantContext,
) -> VoiceSignalResponse:
    access = await _access(
        workspace_id=workspace_id,
        context=context,
    )

    try:
        return await (
            _service(
                workspace_id=workspace_id,
                context=context,
            )
            .signal(
                access=access,
                channel_id=channel_id,
                payload=payload,
            )
        )

    except Exception as exc:
        raise _translate(
            exc
        ) from exc


@router.get(
    "/signals",
    response_model=VoiceSignalPollResponse,
)
async def poll_voice_signals(
    workspace_id: uuid.UUID,
    channel_id: uuid.UUID,
    context: TenantContext,
) -> VoiceSignalPollResponse:
    access = await _access(
        workspace_id=workspace_id,
        context=context,
    )

    try:
        return await (
            _service(
                workspace_id=workspace_id,
                context=context,
            )
            .poll_signals(
                access=access,
                channel_id=channel_id,
            )
        )

    except Exception as exc:
        raise _translate(
            exc
        ) from exc


@router.post(
    "/presence",
    response_model=VoiceRealtimeStateResponse,
)
async def voice_presence_heartbeat(
    workspace_id: uuid.UUID,
    channel_id: uuid.UUID,
    payload: VoicePresenceHeartbeatRequest,
    context: TenantContext,
) -> VoiceRealtimeStateResponse:
    access = await _access(
        workspace_id=workspace_id,
        context=context,
    )

    try:
        return await (
            _service(
                workspace_id=workspace_id,
                context=context,
            )
            .heartbeat(
                access=access,
                channel_id=channel_id,
                payload=payload,
            )
        )

    except Exception as exc:
        raise _translate(
            exc
        ) from exc


@router.post(
    "/speaking",
    response_model=VoiceRealtimeStateResponse,
)
async def update_voice_speaking(
    workspace_id: uuid.UUID,
    channel_id: uuid.UUID,
    payload: VoiceSpeakingRequest,
    context: TenantContext,
) -> VoiceRealtimeStateResponse:
    access = await _access(
        workspace_id=workspace_id,
        context=context,
    )

    try:
        return await (
            _service(
                workspace_id=workspace_id,
                context=context,
            )
            .speaking(
                access=access,
                channel_id=channel_id,
                speaking=payload.speaking,
            )
        )

    except Exception as exc:
        raise _translate(
            exc
        ) from exc


@router.get(
    "/capabilities",
    response_model=VoiceCapabilitiesResponse,
)
async def voice_capabilities(
    workspace_id: uuid.UUID,
    channel_id: uuid.UUID,
    context: TenantContext,
) -> VoiceCapabilitiesResponse:
    await _access(
        workspace_id=workspace_id,
        context=context,
    )

    try:
        await (
            _service(
                workspace_id=workspace_id,
                context=context,
            )
            .require_voice_channel(
                channel_id=channel_id
            )
        )

    except Exception as exc:
        raise _translate(
            exc
        ) from exc

    return VoiceChannelService.capabilities()


__all__ = [
    "router",
]