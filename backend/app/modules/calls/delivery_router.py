from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import time
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_control_db
from app.modules.auth.models import User
from app.modules.auth.permissions import get_current_verified_user
from app.modules.chat.chat_redis import get_chat_redis
from app.modules.chat.models import Conversation, ConversationMember

from .enums import CallParticipantState, CallScope, CallStatus
from .models import RealtimeCall, RealtimeCallParticipant
from .schemas import CallSignalRequest
from .service import CallService


router = APIRouter()

from .call_runtime import call_context, RING_SECONDS

@router.get("/{call_id}/context")
async def get_context_for_call(
    call_id: uuid.UUID,
    session: AsyncSession = Depends(get_control_db),
    user: User = Depends(get_current_verified_user),
):
    call = await CallService(session).get_call_or_404(call_id)
    return await call_context(session, call, user.id)



def display_name(user: User) -> str:
    full_name = " ".join(
        value
        for value in (
            getattr(user, "first_name", None),
            getattr(user, "last_name", None),
        )
        if value
    ).strip()

    return full_name or user.username


async def conversation_context(
    session: AsyncSession,
    conversation_id: uuid.UUID,
    viewer_id: uuid.UUID,
) -> dict:
    await CallService(session).assert_target_access(
        user_id=viewer_id,
        scope=CallScope.CONVERSATION,
        conversation_id=conversation_id,
        channel_id=None,
    )

    conversation = await session.get(
        Conversation,
        conversation_id,
    )

    if conversation is None or not conversation.is_active:
        raise HTTPException(404, "Conversation not found.")

    people = list(
        await session.scalars(
            select(User)
            .join(
                ConversationMember,
                ConversationMember.user_id == User.id,
            )
            .where(
                ConversationMember.conversation_id == conversation_id,
                ConversationMember.left_at.is_(None),
            )
            .order_by(User.id)
        )
    )

    kind = getattr(
        conversation.conversation_type,
        "value",
        conversation.conversation_type,
    )

    peers = [
        person
        for person in people
        if person.id != viewer_id
    ]

    name = (
        conversation.name or "Group call"
        if str(kind).lower() == "group"
        else ", ".join(display_name(person) for person in peers)
        or "Conversation call"
    )

    return {
        "id": str(conversation_id),
        "name": name,
        "conversation_type": str(kind).lower(),
        "members": [
            {
                "user_id": str(person.id),
                "name": display_name(person),
                "username": person.username,
                "avatar_url": person.avatar_url,
            }
            for person in people
        ],
    }


@router.get("/context/{conversation_id}")
async def get_call_context(
    conversation_id: uuid.UUID,
    session: AsyncSession = Depends(get_control_db),
    user: User = Depends(get_current_verified_user),
):
    return await conversation_context(
        session,
        conversation_id,
        user.id,
    )


@router.get("/ice-config")
async def get_ice_configuration(
    user: User = Depends(get_current_verified_user),
):
    servers: list[dict] = [
        {
            "urls": [
                "stun:stun.l.google.com:19302",
            ]
        }
    ]

    turn_urls = [
        value.strip()
        for value in os.getenv(
            "WORKFORCE_TURN_URLS",
            "",
        ).split(",")
        if value.strip()
    ]

    if turn_urls:
        if any(
            not value.startswith(("turn:", "turns:"))
            for value in turn_urls
        ):
            raise HTTPException(
                503,
                "TURN URLs are incorrectly configured.",
            )

        secret = os.getenv(
            "WORKFORCE_TURN_SECRET",
            "",
        )

        if not secret:
            raise HTTPException(
                503,
                "TURN URLs are configured without a TURN secret.",
            )

        expires = int(time.time()) + 3600
        username = f"{expires}:{user.id}"

        credential = base64.b64encode(
            hmac.new(
                secret.encode("utf-8"),
                username.encode("utf-8"),
                hashlib.sha1,
            ).digest()
        ).decode("ascii")

        servers.append(
            {
                "urls": turn_urls,
                "username": username,
                "credential": credential,
            }
        )

    return {
        "ice_servers": servers,
    }


@router.get("/active")
async def get_active_calls(
    session: AsyncSession = Depends(get_control_db),
    user: User = Depends(get_current_verified_user),
):
    from .router import build_call_response

    calls = list(
        await session.scalars(
            select(RealtimeCall)
            .join(
                RealtimeCallParticipant,
                RealtimeCallParticipant.call_id == RealtimeCall.id,
            )
            .where(
                RealtimeCall.scope == CallScope.CONVERSATION,
                RealtimeCall.status.in_(
                    [
                        CallStatus.RINGING,
                        CallStatus.ACTIVE,
                    ]
                ),
                RealtimeCallParticipant.user_id == user.id,
                RealtimeCallParticipant.state.in_(
                    [
                        CallParticipantState.INVITED,
                        CallParticipantState.JOINED,
                    ]
                ),
            )
            .order_by(RealtimeCall.created_at.desc())
            .limit(25)
        )
    )

    cutoff = datetime.now(timezone.utc) - timedelta(seconds=RING_SECONDS)
    items = []

    for call in calls:
        participant = await session.scalar(
            select(RealtimeCallParticipant).where(
                RealtimeCallParticipant.call_id == call.id,
                RealtimeCallParticipant.user_id == user.id,
            )
        )

        if (
            participant is not None
            and participant.state == CallParticipantState.INVITED
            and participant.created_at < cutoff
        ):
            continue

        try:
            context = await call_context(session, call, user.id)
        except HTTPException as exc:
            if exc.status_code in (403, 404):
                continue
            raise

        caller = await session.get(
            User,
            call.started_by_user_id,
        )

        response = await build_call_response(
            call=call,
            session=session,
        )

        item = response.model_dump(mode="json")
        item["can_reply"] = context["can_reply"]
        item["invitation_expires_at"] = (
            participant.created_at + timedelta(seconds=RING_SECONDS)
        ).isoformat() if participant else None
        item["conversation_name"] = context["name"]
        item["caller_name"] = (
            display_name(caller)
            if caller is not None
            else "Caller"
        )
        item["caller_username"] = (
            caller.username
            if caller is not None
            else None
        )
        item["caller_avatar_url"] = (
            caller.avatar_url
            if caller is not None
            else None
        )

        items.append(item)

    return {
        "items": items,
    }


async def require_joined(
    session: AsyncSession,
    call_id: uuid.UUID,
    user_id: uuid.UUID,
):
    service = CallService(session)
    call = await service.get_call_or_404(call_id)

    await service.assert_call_access(
        user_id=user_id,
        call=call,
    )

    if call.status not in (
        CallStatus.RINGING,
        CallStatus.ACTIVE,
    ):
        raise HTTPException(409, "Call is closed.")

    participant = await session.scalar(
        select(RealtimeCallParticipant).where(
            RealtimeCallParticipant.call_id == call_id,
            RealtimeCallParticipant.user_id == user_id,
            RealtimeCallParticipant.state
            == CallParticipantState.JOINED,
        )
    )

    if participant is None:
        raise HTTPException(
            403,
            "Join this call before exchanging media signals.",
        )

    return call


async def store_call_signal(
    session: AsyncSession,
    call_id: uuid.UUID,
    sender_user_id: uuid.UUID,
    payload: CallSignalRequest,
) -> dict:
    await require_joined(
        session,
        call_id,
        sender_user_id,
    )

    await CallService(session).assert_signal_access(
        call_id=call_id,
        sender_user_id=sender_user_id,
        target_user_id=payload.target_user_id,
    )

    if payload.target_user_id == sender_user_id:
        raise HTTPException(422, "Cannot signal yourself.")

    event = {
        "sender_user_id": str(sender_user_id),
        "target_user_id": (
            str(payload.target_user_id)
            if payload.target_user_id
            else None
        ),
        "signal_type": payload.signal_type.value,
        "payload": payload.payload,
    }

    encoded = json.dumps(
        event,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    if len(encoded.encode("utf-8")) > 128 * 1024:
        raise HTTPException(413, "Media signal is too large.")

    key = f"workforce:calls:signals:{call_id}"

    try:
        redis = get_chat_redis()
        pipeline = redis.pipeline(transaction=True)

        pipeline.xadd(
            key,
            {"event": encoded},
            maxlen=10000,
            approximate=True,
        )
        pipeline.expire(key, 21600)

        result = await pipeline.execute()
    except Exception as exc:
        raise HTTPException(
            503,
            "Call signaling storage is unavailable.",
        ) from exc

    signal_id = result[0]

    if isinstance(signal_id, bytes):
        signal_id = signal_id.decode("ascii")

    return {
        "id": str(signal_id),
        **event,
    }


@router.get("/{call_id}/signals")
async def get_call_signals(
    call_id: uuid.UUID,
    cursor: str = Query(
        default="0-0",
        max_length=64,
    ),
    session: AsyncSession = Depends(get_control_db),
    user: User = Depends(get_current_verified_user),
):
    await require_joined(
        session,
        call_id,
        user.id,
    )

    if not re.fullmatch(r"\d+-\d+", cursor):
        raise HTTPException(422, "Invalid signal cursor.")

    try:
        rows = await get_chat_redis().xrange(
            f"workforce:calls:signals:{call_id}",
            min=f"({cursor}",
            max="+",
            count=200,
        )
    except Exception as exc:
        raise HTTPException(
            503,
            "Call signaling storage is unavailable.",
        ) from exc

    items = []
    next_cursor = cursor

    for signal_id, fields in rows:
        if isinstance(signal_id, bytes):
            signal_id = signal_id.decode("ascii")

        next_cursor = str(signal_id)
        encoded = fields.get("event", fields.get(b"event"))
        event = json.loads(encoded)

        if event["sender_user_id"] == str(user.id):
            continue

        if event["target_user_id"] not in (
            None,
            str(user.id),
        ):
            continue

        items.append(
            {
                "id": next_cursor,
                **event,
            }
        )

    return {
        "items": items,
        "next_cursor": next_cursor,
    }