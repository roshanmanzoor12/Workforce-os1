from __future__ import annotations

import asyncio
import logging
import time
import uuid

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from pydantic import (
    BaseModel,
    ConfigDict,
    ValidationError,
)
from sqlalchemy import select

from app.core.database import ControlSessionLocal
from app.modules.auth.models import User
from app.modules.auth.permissions import (
    get_current_verified_user,
)

from .chat_redis import get_chat_redis
from .connection_manager import chat_connection_manager
from .pagination_schemas import ChatMessagePagePublic
from .realtime_client_protocol import (
    RealtimeClientCommandType,
    RealtimeServerEventType,
)
from .realtime_client_schemas import (
    RealtimeClientCommand,
    RealtimeServerEnvelope,
)
from .realtime_presence import RealtimePresenceTracker
from .realtime_publish_service import ChatRealtimePublishService
from .realtime_resume import RealtimeResumeService
from .schemas import ChatMessagePublic
from .service import (
    ChatPermissionError,
    ConversationNotFoundError,
)
from .typing_command_service import TypingCommandService
from .typing_service import TypingService
from .websocket_ticket import WebSocketTicketService


logger = logging.getLogger(__name__)

MAX_MESSAGE_BYTES = 4096
ACCOUNT_CHECK_SECONDS = 20.0
SEND_TIMEOUT_SECONDS = 10.0


router = APIRouter(
    prefix="/chat/realtime",
    tags=["Chat Realtime"],
)


class WebSocketTicketResponse(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    ticket: str
    expires_in_seconds: int


@router.post(
    "/ticket",
    response_model=WebSocketTicketResponse,
)
async def create_realtime_ticket(
    user: User = Depends(
        get_current_verified_user
    ),
) -> WebSocketTicketResponse:
    service = WebSocketTicketService(
        get_chat_redis()
    )

    try:
        ticket = await service.issue(
            user_id=user.id,
        )

    except Exception as exc:
        logger.exception(
            "Realtime ticket issuance failed"
        )

        raise HTTPException(
            status_code=503,
            detail="Realtime ticket service is unavailable.",
        ) from exc

    return WebSocketTicketResponse(
        ticket=ticket,
        expires_in_seconds=service.ttl_seconds,
    )


async def _account_is_eligible(
    user_id: uuid.UUID,
) -> bool:
    async with ControlSessionLocal() as session:
        result = await session.scalar(
            select(User.id).where(
                User.id == user_id,
                User.is_active.is_(True),
                User.is_locked.is_(False),
                User.is_email_verified.is_(True),
            )
        )

        return result is not None


async def _close_socket(
    websocket: WebSocket,
    code: int,
) -> None:
    try:
        await asyncio.wait_for(
            websocket.close(code=code),
            timeout=2.0,
        )

    except asyncio.CancelledError:
        raise

    except Exception:
        pass


async def _send_text(
    websocket: WebSocket,
    payload: str,
) -> None:
    await asyncio.wait_for(
        websocket.send_text(payload),
        timeout=SEND_TIMEOUT_SECONDS,
    )


async def _send_envelope(
    websocket: WebSocket,
    event_type: RealtimeServerEventType,
    data: dict,
) -> None:
    envelope = RealtimeServerEnvelope(
        event=event_type,
        data=data,
    )

    await _send_text(
        websocket,
        envelope.model_dump_json(),
    )


async def _handle_command(
    websocket: WebSocket,
    *,
    user_id: uuid.UUID,
    text: str,
    redis_client,
    presence: RealtimePresenceTracker,
) -> None:
    # Preserve the original text heartbeat protocol.
    if text == "ping":
        await presence.heartbeat(
            user_id=user_id,
        )

        await _send_text(
            websocket,
            "pong",
        )

        return

    try:
        command = RealtimeClientCommand.model_validate_json(
            text
        )

    except ValidationError:
        await _send_envelope(
            websocket,
            RealtimeServerEventType.COMMAND_REJECTED,
            {
                "code": "INVALID_COMMAND",
                "message": "Send a valid realtime command.",
            },
        )

        return

    if command.command == RealtimeClientCommandType.PING:
        timestamp = await presence.heartbeat(
            user_id=user_id,
        )

        await _send_envelope(
            websocket,
            RealtimeServerEventType.PONG,
            {
                "heartbeat_unix": timestamp,
            },
        )

        return

    if command.conversation_id is None:
        await _send_envelope(
            websocket,
            RealtimeServerEventType.COMMAND_REJECTED,
            {
                "code": "CONVERSATION_REQUIRED",
                "message": "conversation_id is required.",
            },
        )

        return

    try:
        async with ControlSessionLocal() as session:
            if command.command in {
                RealtimeClientCommandType.TYPING_START,
                RealtimeClientCommandType.TYPING_STOP,
            }:
                service = TypingCommandService(
                    session,
                    typing_service=TypingService(
                        redis_client
                    ),
                )

                action = (
                    service.start
                    if command.command
                    == RealtimeClientCommandType.TYPING_START
                    else service.stop
                )

                await action(
                    conversation_id=command.conversation_id,
                    user_id=user_id,
                )

                data = {
                    "command": command.command.value,
                    "conversation_id": str(
                        command.conversation_id
                    ),
                }

            elif command.command == RealtimeClientCommandType.RESUME:
                result = (
                    await RealtimeResumeService(
                        session
                    ).resume_conversation(
                        conversation_id=command.conversation_id,
                        user_id=user_id,
                        cursor=command.cursor,
                        limit=50,
                    )
                )

                page = ChatMessagePagePublic(
                    items=[
                        ChatMessagePublic.model_validate(
                            message
                        )
                        for message in result.page.items
                    ],
                    next_cursor=result.page.next_cursor,
                    has_more=result.page.has_more,
                )

                data = {
                    "command": command.command.value,
                    "conversation_id": str(
                        command.conversation_id
                    ),
                    "page": page.model_dump(
                        mode="json"
                    ),
                }

            else:
                raise ValueError(
                    "Unsupported command."
                )

    except (
        ChatPermissionError,
        ConversationNotFoundError,
    ):
        await _send_envelope(
            websocket,
            RealtimeServerEventType.COMMAND_REJECTED,
            {
                "code": "CONVERSATION_UNAVAILABLE",
                "message": "Conversation access is unavailable.",
            },
        )

        return

    except ValueError:
        await _send_envelope(
            websocket,
            RealtimeServerEventType.COMMAND_REJECTED,
            {
                "code": "INVALID_COMMAND",
                "message": "Command parameters are invalid.",
            },
        )

        return

    await _send_envelope(
        websocket,
        RealtimeServerEventType.COMMAND_ACCEPTED,
        data,
    )


@router.websocket("/ws")
async def chat_realtime_websocket(
    websocket: WebSocket,
) -> None:
    ticket = websocket.query_params.get(
        "ticket",
        "",
    ).strip()

    if not ticket or len(ticket) > 512:
        await _close_socket(
            websocket,
            status.WS_1008_POLICY_VIOLATION,
        )

        return

    try:
        redis_client = get_chat_redis()

        user_id = await WebSocketTicketService(
            redis_client
        ).consume(
            token=ticket,
        )

        if user_id is None:
            await _close_socket(
                websocket,
                status.WS_1008_POLICY_VIOLATION,
            )

            return

        if not await _account_is_eligible(user_id):
            await _close_socket(
                websocket,
                status.WS_1008_POLICY_VIOLATION,
            )

            return

    except Exception:
        logger.exception(
            "Realtime connection authentication failed"
        )

        await _close_socket(
            websocket,
            status.WS_1011_INTERNAL_ERROR,
        )

        return

    presence = RealtimePresenceTracker(
        redis_client
    )

    publisher = ChatRealtimePublishService()
    registered = False

    try:
        await chat_connection_manager.connect(
            user_id=user_id,
            websocket=websocket,
            accept=True,
        )

        registered = True

        await presence.heartbeat(
            user_id=user_id,
        )

        await publisher.presence_updated(
            actor_user_id=user_id,
            online=True,
        )

        last_account_check = time.monotonic()

        while True:
            if (
                time.monotonic() - last_account_check
                >= ACCOUNT_CHECK_SECONDS
            ):
                if not await _account_is_eligible(user_id):
                    await _close_socket(
                        websocket,
                        status.WS_1008_POLICY_VIOLATION,
                    )

                    break

                await presence.heartbeat(
                    user_id=user_id,
                )

                last_account_check = time.monotonic()

            try:
                message = await asyncio.wait_for(
                    websocket.receive(),
                    timeout=ACCOUNT_CHECK_SECONDS,
                )

            except asyncio.TimeoutError:
                continue

            message_type = message.get("type")

            if message_type == "websocket.disconnect":
                break

            if message_type != "websocket.receive":
                continue

            text = message.get("text")

            if text is None:
                await _close_socket(
                    websocket,
                    status.WS_1003_UNSUPPORTED_DATA,
                )

                break

            if len(text.encode("utf-8")) > MAX_MESSAGE_BYTES:
                await _close_socket(
                    websocket,
                    status.WS_1009_MESSAGE_TOO_BIG,
                )

                break

            await _handle_command(
                websocket,
                user_id=user_id,
                text=text,
                redis_client=redis_client,
                presence=presence,
            )

    except WebSocketDisconnect:
        pass

    except asyncio.CancelledError:
        raise

    except Exception:
        logger.exception(
            "Realtime socket processing failed for user %s",
            user_id,
        )

        await _close_socket(
            websocket,
            status.WS_1011_INTERNAL_ERROR,
        )

    finally:
        if registered:
            await chat_connection_manager.disconnect(
                user_id=user_id,
                websocket=websocket,
            )

            try:
                remaining = (
                    await chat_connection_manager.connection_count(
                        user_id=user_id,
                    )
                )

                if remaining == 0:
                    await presence.mark_offline(
                        user_id=user_id,
                    )

                    # A new local connection may have arrived
                    # while the offline operation awaited Redis.
                    if await chat_connection_manager.is_connected(
                        user_id=user_id,
                    ):
                        await presence.heartbeat(
                            user_id=user_id,
                        )

                    else:
                        await publisher.presence_updated(
                            actor_user_id=user_id,
                            online=False,
                        )

            except Exception:
                logger.exception(
                    "Realtime presence cleanup failed for user %s",
                    user_id,
                )


__all__ = [
    "WebSocketTicketResponse",
    "router",
]