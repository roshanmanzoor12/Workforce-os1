from __future__ import annotations

import uuid
from app.modules.calls.delivery_router import (
    router as delivery_router,
    store_call_signal,
)
from fastapi import (
    APIRouter,
    Depends,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_control_db
from app.modules.auth.permissions import (
    get_current_verified_user,
)
from app.modules.calls.repository import (
    CallRepository,
)
from app.modules.calls.schemas import (
    CallHeartbeatRequest,
    CallHeartbeatResponse,
    CallMediaStateRequest,
    CallParticipantResponse,
    CallParticipantsResponse,
    CallResponse,
    CallSignalRequest,
    CallSignalResponse,
    CreateCallRequest,
)
from app.modules.calls.service import (
    CallService,
)
from app.modules.calls.signaling import (
    build_call_signal_event,
)


from .call_runtime import call_lifespan

# call-repair-v3
router = APIRouter(
    lifespan=call_lifespan,
    prefix="/calls",
    tags=["calls"],
)

router.include_router(delivery_router)
from .personal_router import router as personal_calls_router
router.include_router(personal_calls_router)

def user_id_from(
    user: object,
) -> uuid.UUID:
    value = getattr(
        user,
        "id",
    )

    if isinstance(
        value,
        uuid.UUID,
    ):
        return value

    return uuid.UUID(
        str(value)
    )


def call_service(
    session: AsyncSession,
) -> CallService:
    return CallService(
        session
    )


async def build_call_response(
    *,
    call,
    session: AsyncSession,
) -> CallResponse:
    repository = CallRepository(
        session
    )

    participants = (
        await repository.list_participants(
            call_id=call.id
        )
    )

    return CallResponse(
        id=call.id,
        scope=call.scope,
        conversation_id=(
            call.conversation_id
        ),
        channel_id=call.channel_id,
        started_by_user_id=(
            call.started_by_user_id
        ),
        kind=call.kind,
        status=call.status,
        created_at=call.created_at,
        started_at=call.started_at,
        ended_at=call.ended_at,
        participants=[
            CallParticipantResponse
            .model_validate(item)
            for item in participants
        ],
    )


@router.post(
    "",
    response_model=CallResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_call(
    payload: CreateCallRequest,
    session: AsyncSession = Depends(
        get_control_db
    ),
    current_user=Depends(
        get_current_verified_user
    ),
) -> CallResponse:
    call = await call_service(
        session
    ).create_call(
        user_id=user_id_from(
            current_user
        ),
        payload=payload,
    )

    return await build_call_response(
        call=call,
        session=session,
    )


@router.get(
    "/{call_id}",
    response_model=CallResponse,
)
async def get_call(
    call_id: uuid.UUID,
    session: AsyncSession = Depends(
        get_control_db
    ),
    current_user=Depends(
        get_current_verified_user
    ),
) -> CallResponse:
    service = call_service(
        session
    )

    call = await service.get_call_or_404(
        call_id
    )

    await service.assert_call_access(
        user_id=user_id_from(
            current_user
        ),
        call=call,
    )

    return await build_call_response(
        call=call,
        session=session,
    )


@router.get(
    "/{call_id}/participants",
    response_model=(
        CallParticipantsResponse
    ),
)
async def list_call_participants(
    call_id: uuid.UUID,
    session: AsyncSession = Depends(
        get_control_db
    ),
    current_user=Depends(
        get_current_verified_user
    ),
) -> CallParticipantsResponse:
    service = call_service(
        session
    )

    call = await service.get_call_or_404(
        call_id
    )

    await service.assert_call_access(
        user_id=user_id_from(
            current_user
        ),
        call=call,
    )

    participants = (
        await CallRepository(
            session
        ).list_participants(
            call_id=call_id
        )
    )

    return CallParticipantsResponse(
        call_id=call_id,
        participants=[
            CallParticipantResponse
            .model_validate(item)
            for item in participants
        ],
    )


@router.post(
    "/{call_id}/join",
    response_model=CallParticipantResponse,
)
async def join_call(
    call_id: uuid.UUID,
    session: AsyncSession = Depends(
        get_control_db
    ),
    current_user=Depends(
        get_current_verified_user
    ),
) -> CallParticipantResponse:
    participant = await call_service(
        session
    ).join(
        call_id=call_id,
        user_id=user_id_from(
            current_user
        ),
    )

    return (
        CallParticipantResponse
        .model_validate(
            participant
        )
    )


@router.post(
    "/{call_id}/heartbeat",
    response_model=CallHeartbeatResponse,
)
async def call_heartbeat(
    call_id: uuid.UUID,
    payload: CallHeartbeatRequest,
    session: AsyncSession = Depends(
        get_control_db
    ),
    current_user=Depends(
        get_current_verified_user
    ),
) -> CallHeartbeatResponse:
    current_user_id = user_id_from(
        current_user
    )

    timestamp = await call_service(
        session
    ).heartbeat(
        call_id=call_id,
        user_id=current_user_id,
        connection_id=payload.connection_id,
    )

    return CallHeartbeatResponse(
        call_id=call_id,
        user_id=current_user_id,
        alive=True,
        timestamp=timestamp,
    )


@router.patch(
    "/{call_id}/media-state",
    response_model=CallParticipantResponse,
)
async def update_media_state(
    call_id: uuid.UUID,
    payload: CallMediaStateRequest,
    session: AsyncSession = Depends(
        get_control_db
    ),
    current_user=Depends(
        get_current_verified_user
    ),
) -> CallParticipantResponse:
    participant = await call_service(
        session
    ).update_media_state(
        call_id=call_id,
        user_id=user_id_from(
            current_user
        ),
        microphone_enabled=(
            payload.microphone_enabled
        ),
        camera_enabled=(
            payload.camera_enabled
        ),
    )

    return CallParticipantResponse.model_validate(
        participant
    )


@router.post(
    "/{call_id}/leave",
    response_model=CallParticipantResponse,
)
async def leave_call(
    call_id: uuid.UUID,
    session: AsyncSession = Depends(
        get_control_db
    ),
    current_user=Depends(
        get_current_verified_user
    ),
) -> CallParticipantResponse:
    participant = await call_service(
        session
    ).leave(
        call_id=call_id,
        user_id=user_id_from(
            current_user
        ),
    )

    return (
        CallParticipantResponse
        .model_validate(
            participant
        )
    )


@router.post(
    "/{call_id}/decline",
    response_model=CallParticipantResponse,
)
async def decline_call(
    call_id: uuid.UUID,
    session: AsyncSession = Depends(
        get_control_db
    ),
    current_user=Depends(
        get_current_verified_user
    ),
) -> CallParticipantResponse:
    participant = await call_service(
        session
    ).decline(
        call_id=call_id,
        user_id=user_id_from(
            current_user
        ),
    )

    return (
        CallParticipantResponse
        .model_validate(
            participant
        )
    )


@router.post(
    "/{call_id}/end",
    response_model=CallResponse,
)
async def end_call(
    call_id: uuid.UUID,
    session: AsyncSession = Depends(
        get_control_db
    ),
    current_user=Depends(
        get_current_verified_user
    ),
) -> CallResponse:
    call = await call_service(
        session
    ).end_call(
        call_id=call_id,
        user_id=user_id_from(
            current_user
        ),
    )

    return await build_call_response(
        call=call,
        session=session,
    )


@router.post(
    "/{call_id}/screen-share/start",
    response_model=CallParticipantResponse,
)
async def start_screen_share(
    call_id: uuid.UUID,
    session: AsyncSession = Depends(
        get_control_db
    ),
    current_user=Depends(
        get_current_verified_user
    ),
) -> CallParticipantResponse:
    participant = await call_service(
        session
    ).set_screen_share(
        call_id=call_id,
        user_id=user_id_from(
            current_user
        ),
        active=True,
    )

    return (
        CallParticipantResponse
        .model_validate(
            participant
        )
    )


@router.post(
    "/{call_id}/screen-share/stop",
    response_model=CallParticipantResponse,
)
async def stop_screen_share(
    call_id: uuid.UUID,
    session: AsyncSession = Depends(
        get_control_db
    ),
    current_user=Depends(
        get_current_verified_user
    ),
) -> CallParticipantResponse:
    participant = await call_service(
        session
    ).set_screen_share(
        call_id=call_id,
        user_id=user_id_from(
            current_user
        ),
        active=False,
    )

    return (
        CallParticipantResponse
        .model_validate(
            participant
        )
    )


@router.post(
    "/{call_id}/signal",
    response_model=CallSignalResponse,
)
async def create_call_signal(
    call_id: uuid.UUID,
    payload: CallSignalRequest,
    session: AsyncSession = Depends(get_control_db),
    current_user=Depends(get_current_verified_user),
) -> CallSignalResponse:
    event = await store_call_signal(
        session=session,
        call_id=call_id,
        sender_user_id=user_id_from(current_user),
        payload=payload,
    )

    return CallSignalResponse(
        event={
            "type": "call.signal",
            "data": {
                "call_id": str(call_id),
                **event,
            },
        }
    )