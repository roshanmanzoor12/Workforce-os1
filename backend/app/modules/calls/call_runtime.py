
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager, suppress
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import and_, or_, select

from app.core.database import get_control_db
from app.modules.auth.models import User
from app.modules.chat.models import Conversation, ConversationMember
from .enums import CallParticipantState as P, CallScope, CallStatus as S, ScreenShareState
from .models import RealtimeCall, RealtimeCallParticipant

RING_SECONDS = 40


async def expire_call(session, call):
    """Caller holds the call row lock; join and invite take the same lock."""
    if call.scope != CallScope.CONVERSATION or call.status not in (S.RINGING, S.ACTIVE):
        return

    now = datetime.now(timezone.utc)

    people = list(
        await session.scalars(
            select(RealtimeCallParticipant).where(
                RealtimeCallParticipant.call_id == call.id,
            )
        )
    )

    for person in people:
        if (
            person.state == P.INVITED
            and now >= person.created_at + timedelta(seconds=RING_SECONDS)
        ):
            person.state = P.LEFT
            person.left_at = (
                person.created_at + timedelta(seconds=RING_SECONDS)
            )
            person.screen_share_state = ScreenShareState.STOPPED

    others = [
        person for person in people
        if person.user_id != call.started_by_user_id
    ]

    answered = any(
        person.joined_at is not None
        for person in others
    )

    waiting = any(
        person.state == P.INVITED
        for person in others
    )

    if (
        not answered
        and not waiting
        and now >= call.created_at + timedelta(seconds=RING_SECONDS)
    ):
        call.status = S.CANCELLED
        call.ended_at = now

        for person in people:
            if person.state == P.JOINED:
                person.state = P.LEFT
                person.left_at = now
                person.screen_share_state = ScreenShareState.STOPPED

    await session.flush()


async def call_context(session, call, viewer_id):
    from .service import CallService

    await CallService(session).assert_call_access(
        user_id=viewer_id,
        call=call,
    )

    if call.scope != CallScope.CONVERSATION:
        raise HTTPException(
            400,
            "Use workspace call controls for a channel call.",
        )

    conversation = await session.get(
        Conversation,
        call.conversation_id,
    )

    if conversation is None:
        raise HTTPException(404, "Conversation not found.")

    kind = str(
        getattr(
            conversation.conversation_type,
            "value",
            conversation.conversation_type,
        )
    ).lower()

    participants = list(
        await session.scalars(
            select(RealtimeCallParticipant).where(
                RealtimeCallParticipant.call_id == call.id,
            )
        )
    )

    ids = {
        person.user_id
        for person in participants
    }

    people = list(
        await session.scalars(
            select(User)
            .where(User.id.in_(ids))
            .order_by(User.id)
        )
    )

    def name(person):
        return (
            " ".join(
                filter(
                    None,
                    [
                        person.first_name,
                        person.last_name,
                    ],
                )
            ).strip()
            or person.username
        )

    member = await session.scalar(
        select(ConversationMember.id).where(
            ConversationMember.conversation_id == call.conversation_id,
            ConversationMember.user_id == viewer_id,
            ConversationMember.left_at.is_(None),
        )
    )

    return {
        "id": str(call.conversation_id),
        "name": (
            conversation.name or "Group call"
            if kind == "group"
            else ", ".join(
                name(person)
                for person in people
                if person.id != viewer_id
            ) or "Personal call"
        ),
        "conversation_type": kind,
        "can_reply": member is not None,
        "members": [
            {
                "user_id": str(person.id),
                "name": name(person),
                "username": person.username,
                "avatar_url": person.avatar_url,
            }
            for person in people
        ],
    }


@asynccontextmanager
async def call_lifespan(app):
    logging.getLogger("uvicorn.error").info(
        "Call invitation expiry worker active (40 seconds)"
    )

    async def sweep():
        while True:
            try:
                async with asynccontextmanager(get_control_db)() as session:
                    cutoff = (
                        datetime.now(timezone.utc)
                        - timedelta(seconds=RING_SECONDS)
                    )

                    expired = select(
                        RealtimeCallParticipant.id
                    ).where(
                        RealtimeCallParticipant.call_id == RealtimeCall.id,
                        RealtimeCallParticipant.state == P.INVITED,
                        RealtimeCallParticipant.created_at <= cutoff,
                    ).exists()

                    answered = select(
                        RealtimeCallParticipant.id
                    ).where(
                        RealtimeCallParticipant.call_id == RealtimeCall.id,
                        RealtimeCallParticipant.user_id
                        != RealtimeCall.started_by_user_id,
                        RealtimeCallParticipant.joined_at.is_not(None),
                    ).exists()

                    calls = list(
                        await session.scalars(
                            select(RealtimeCall)
                            .where(
                                RealtimeCall.scope == CallScope.CONVERSATION,
                                RealtimeCall.status.in_([
                                    S.RINGING,
                                    S.ACTIVE,
                                ]),
                                or_(
                                    expired,
                                    and_(
                                        RealtimeCall.created_at <= cutoff,
                                        ~answered,
                                    ),
                                ),
                            )
                            .with_for_update(skip_locked=True)
                        )
                    )

                    for call in calls:
                        await expire_call(session, call)

                    await session.commit()

            except asyncio.CancelledError:
                raise

            except Exception:
                logging.getLogger(__name__).exception(
                    "Call invitation expiry failed"
                )

            await asyncio.sleep(1)

    task = asyncio.create_task(sweep())

    try:
        yield
    finally:
        task.cancel()

        with suppress(asyncio.CancelledError):
            await task
