"""Additive API for message metadata and conversation state."""
from __future__ import annotations

import uuid
from collections import Counter
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_control_db
from app.modules.auth.models import User
from app.modules.auth.permissions import get_current_verified_user

from .features_models import (
    ChatConversationPreference, ChatMessageDelivery, ChatMessageFeature,
    ChatMessagePin, ChatMessageReaction,
)
from .features_schemas import (
    ConversationFeatureSummary, ConversationPreferencePatch, DeliveryPublic,
    FeatureMessageCreate, FeatureMessagePublic, ReactionRequest,
)
from .models import ChatMessage, ConversationMember
from .realtime_enums import ChatRealtimeEventType
from .realtime_events import ChatRealtimeEvent
from .realtime_publish_service import ChatRealtimePublishService
from .service import ChatPermissionError, ChatService, ConversationNotFoundError

router = APIRouter(prefix="/chat", tags=["Chat features"])


async def _member(session: AsyncSession, conversation_id: uuid.UUID, user_id: uuid.UUID) -> ConversationMember:
    row = await session.scalar(select(ConversationMember).where(
        ConversationMember.conversation_id == conversation_id,
        ConversationMember.user_id == user_id,
        ConversationMember.left_at.is_(None),
    ))
    if row is None:
        raise HTTPException(status_code=403, detail="User is not an active member of this conversation.")
    return row


async def _message(session: AsyncSession, conversation_id: uuid.UUID, message_id: uuid.UUID) -> ChatMessage:
    row = await session.scalar(select(ChatMessage).where(
        ChatMessage.id == message_id, ChatMessage.conversation_id == conversation_id,
    ))
    if row is None:
        raise HTTPException(status_code=404, detail="Message not found.")
    return row


async def _enrich(
    session: AsyncSession,
    message: ChatMessage,
    viewer_id: uuid.UUID,
) -> FeatureMessagePublic:
    from .models import ChatMessageReceipt

    feature = await session.scalar(
        select(ChatMessageFeature).where(
            ChatMessageFeature.message_id == message.id,
        )
    )

    reactions = list(
        await session.scalars(
            select(ChatMessageReaction).where(
                ChatMessageReaction.message_id == message.id,
            )
        )
    )

    pin = await session.scalar(
        select(ChatMessagePin).where(
            ChatMessagePin.message_id == message.id,
        )
    )

    if message.sender_user_id == viewer_id:
        delivered_at = await session.scalar(
            select(
                func.min(ChatMessageDelivery.delivered_at)
            ).where(
                ChatMessageDelivery.message_id == message.id,
                ChatMessageDelivery.user_id != viewer_id,
            )
        )

        read_at = await session.scalar(
            select(
                func.min(ChatMessageReceipt.read_at)
            ).where(
                ChatMessageReceipt.message_id == message.id,
                ChatMessageReceipt.user_id != viewer_id,
            )
        )
    else:
        delivery = await session.scalar(
            select(ChatMessageDelivery).where(
                ChatMessageDelivery.message_id == message.id,
                ChatMessageDelivery.user_id == viewer_id,
            )
        )

        delivered_at = (
            delivery.delivered_at if delivery else None
        )

        read_at = (
            delivery.read_at if delivery else None
        )

    return FeatureMessagePublic(
        **{
            name: getattr(message, name)
            for name in (
                "id",
                "conversation_id",
                "sender_user_id",
                "message_type",
                "content",
                "edited_at",
                "deleted_at",
                "created_at",
            )
        },
        client_message_id=(
            feature.client_message_id if feature else None
        ),
        reply_to_message_id=(
            feature.reply_to_message_id if feature else None
        ),
        reactions=dict(
            Counter(item.emoji for item in reactions)
        ),
        pinned=pin is not None,
        delivered_at=delivered_at,
        read_at=read_at,
    )


async def _event(event_type: ChatRealtimeEventType, conversation_id: uuid.UUID, actor: uuid.UUID, data: dict) -> None:
    await ChatRealtimePublishService().publish_best_effort(ChatRealtimeEvent(
        event_type=event_type, conversation_id=conversation_id, actor_user_id=actor, data=data,
    ))


@router.post("/{conversation_id}/messages/features", response_model=FeatureMessagePublic, status_code=201)
async def send_feature_message(conversation_id: uuid.UUID, request: FeatureMessageCreate,
                               session: AsyncSession = Depends(get_control_db),
                               user: User = Depends(get_current_verified_user)) -> FeatureMessagePublic:
    await _member(session, conversation_id, user.id)
    if request.reply_to_message_id is not None:
        await _message(session, conversation_id, request.reply_to_message_id)
    existing = await session.scalar(select(ChatMessageFeature).where(
        ChatMessageFeature.conversation_id == conversation_id,
        ChatMessageFeature.sender_user_id == user.id,
        ChatMessageFeature.client_message_id == request.client_message_id,
    ))
    if existing:
        message = await _message(session, conversation_id, existing.message_id)
        return await _enrich(session, message, user.id)
    message = ChatMessage(conversation_id=conversation_id, sender_user_id=user.id, content=request.content.strip())
    session.add(message)
    await session.flush()
    session.add(ChatMessageFeature(message_id=message.id, conversation_id=conversation_id, sender_user_id=user.id,
                                    client_message_id=request.client_message_id, reply_to_message_id=request.reply_to_message_id))
    try:
        await session.commit()
    except IntegrityError:
        # The unique client id is the race-safe idempotency boundary.  A
        # concurrent retry can lose the insert race; return the winner rather
        # than creating a second message or returning a 500.
        await session.rollback()
        winner = await session.scalar(select(ChatMessageFeature).where(
            ChatMessageFeature.conversation_id == conversation_id,
            ChatMessageFeature.sender_user_id == user.id,
            ChatMessageFeature.client_message_id == request.client_message_id,
        ))
        if winner is None:
            raise
        return await _enrich(session, await _message(session, conversation_id, winner.message_id), user.id)
    await _event(ChatRealtimeEventType.MESSAGE_CREATED, conversation_id, user.id, {"message_id": str(message.id), "client_message_id": str(request.client_message_id)})
    return await _enrich(session, message, user.id)


@router.get(
    "/{conversation_id}/messages/features",
    response_model=list[FeatureMessagePublic],
)
async def list_feature_messages(
    conversation_id: uuid.UUID,
    session: AsyncSession = Depends(get_control_db),
    user: User = Depends(get_current_verified_user),
) -> list[FeatureMessagePublic]:
    await _member(
        session,
        conversation_id,
        user.id,
    )

    messages = list(
        await session.scalars(
            select(ChatMessage)
            .where(
                ChatMessage.conversation_id
                == conversation_id,
                ChatMessage.deleted_at.is_(None),
            )
            .order_by(
                ChatMessage.created_at.desc(),
                ChatMessage.id.desc(),
            )
            .limit(100)
        )
    )

    messages.reverse()

    return [
        await _enrich(
            session,
            item,
            user.id,
        )
        for item in messages
    ]


@router.put("/{conversation_id}/messages/{message_id}/reactions", status_code=204)
async def add_reaction(conversation_id: uuid.UUID, message_id: uuid.UUID, request: ReactionRequest,
                       session: AsyncSession = Depends(get_control_db), user: User = Depends(get_current_verified_user)) -> None:
    await _member(session, conversation_id, user.id); await _message(session, conversation_id, message_id)
    exists = await session.scalar(select(ChatMessageReaction).where(ChatMessageReaction.message_id == message_id,
                                                                      ChatMessageReaction.user_id == user.id,
                                                                      ChatMessageReaction.emoji == request.emoji))
    if not exists: session.add(ChatMessageReaction(message_id=message_id, user_id=user.id, emoji=request.emoji))
    await session.commit(); await _event(ChatRealtimeEventType.MESSAGE_REACTION, conversation_id, user.id, {"message_id": str(message_id), "emoji": request.emoji, "action": "add"})


@router.delete("/{conversation_id}/messages/{message_id}/reactions/{emoji}", status_code=204)
async def remove_reaction(conversation_id: uuid.UUID, message_id: uuid.UUID, emoji: str,
                          session: AsyncSession = Depends(get_control_db), user: User = Depends(get_current_verified_user)) -> None:
    await _member(session, conversation_id, user.id); await _message(session, conversation_id, message_id)
    await session.execute(delete(ChatMessageReaction).where(ChatMessageReaction.message_id == message_id,
                                                             ChatMessageReaction.user_id == user.id,
                                                             ChatMessageReaction.emoji == emoji))
    await session.commit(); await _event(ChatRealtimeEventType.MESSAGE_REACTION, conversation_id, user.id, {"message_id": str(message_id), "emoji": emoji, "action": "remove"})


@router.put("/{conversation_id}/messages/{message_id}/pin", status_code=204)
async def pin_message(conversation_id: uuid.UUID, message_id: uuid.UUID,
                      session: AsyncSession = Depends(get_control_db), user: User = Depends(get_current_verified_user)) -> None:
    await _member(session, conversation_id, user.id); await _message(session, conversation_id, message_id)
    if not await session.scalar(select(ChatMessagePin).where(ChatMessagePin.message_id == message_id)):
        session.add(ChatMessagePin(message_id=message_id, pinned_by_user_id=user.id))
    await session.commit(); await _event(ChatRealtimeEventType.MESSAGE_PIN, conversation_id, user.id, {"message_id": str(message_id), "pinned": True})


@router.delete("/{conversation_id}/messages/{message_id}/pin", status_code=204)
async def unpin_message(conversation_id: uuid.UUID, message_id: uuid.UUID,
                        session: AsyncSession = Depends(get_control_db), user: User = Depends(get_current_verified_user)) -> None:
    await _member(session, conversation_id, user.id); await _message(session, conversation_id, message_id)
    await session.execute(delete(ChatMessagePin).where(ChatMessagePin.message_id == message_id)); await session.commit()
    await _event(ChatRealtimeEventType.MESSAGE_PIN, conversation_id, user.id, {"message_id": str(message_id), "pinned": False})


@router.patch("/{conversation_id}/preferences", response_model=ConversationFeatureSummary)
async def update_preferences(conversation_id: uuid.UUID, request: ConversationPreferencePatch,
                             session: AsyncSession = Depends(get_control_db), user: User = Depends(get_current_verified_user)) -> ConversationFeatureSummary:
    await _member(session, conversation_id, user.id)
    pref = await session.scalar(select(ChatConversationPreference).where(ChatConversationPreference.conversation_id == conversation_id,
                                                                           ChatConversationPreference.user_id == user.id))
    if pref is None: pref = ChatConversationPreference(conversation_id=conversation_id, user_id=user.id); session.add(pref)
    for key in ("pinned", "muted", "archived"):
        value = getattr(request, key)
        if value is not None: setattr(pref, key, value)
    await session.commit()
    return await _summary(session, conversation_id, user.id)


async def _summary(session: AsyncSession, conversation_id: uuid.UUID, user_id: uuid.UUID) -> ConversationFeatureSummary:
    pref = await session.scalar(select(ChatConversationPreference).where(ChatConversationPreference.conversation_id == conversation_id,
                                                                           ChatConversationPreference.user_id == user_id))
    last_read = pref.last_read_at if pref else None
    query = select(func.count(ChatMessage.id)).join(ConversationMember, ConversationMember.conversation_id == ChatMessage.conversation_id).where(
        ChatMessage.conversation_id == conversation_id, ChatMessage.sender_user_id != user_id,
        ConversationMember.user_id == user_id, ConversationMember.left_at.is_(None), ChatMessage.deleted_at.is_(None))
    if last_read is not None: query = query.where(ChatMessage.created_at > last_read)
    count = int((await session.scalar(query)) or 0)
    return ConversationFeatureSummary(conversation_id=conversation_id, unread_count=count, pinned=bool(pref and pref.pinned),
                                      muted=bool(pref and pref.muted), archived=bool(pref and pref.archived), last_read_at=last_read)


@router.get("/conversations/features", response_model=list[ConversationFeatureSummary])
async def conversation_features(session: AsyncSession = Depends(get_control_db), user: User = Depends(get_current_verified_user)) -> list[ConversationFeatureSummary]:
    ids = list(await session.scalars(select(ConversationMember.conversation_id).where(ConversationMember.user_id == user.id, ConversationMember.left_at.is_(None))))
    return [await _summary(session, item, user.id) for item in ids]


@router.post("/{conversation_id}/messages/{message_id}/delivered", response_model=DeliveryPublic)
async def mark_delivered(conversation_id: uuid.UUID, message_id: uuid.UUID, session: AsyncSession = Depends(get_control_db), user: User = Depends(get_current_verified_user)) -> DeliveryPublic:
    await _member(session, conversation_id, user.id); await _message(session, conversation_id, message_id)
    row = await session.scalar(select(ChatMessageDelivery).where(ChatMessageDelivery.message_id == message_id, ChatMessageDelivery.user_id == user.id))
    if row is None: row = ChatMessageDelivery(message_id=message_id, user_id=user.id); session.add(row)
    await session.commit(); await _event(ChatRealtimeEventType.MESSAGE_DELIVERED, conversation_id, user.id, {"message_id": str(message_id)})
    return DeliveryPublic.model_validate(row)




@router.post("/{conversation_id}/read-through/{message_id}", response_model=ConversationFeatureSummary)
async def mark_read_through(
    conversation_id: uuid.UUID,
    message_id: uuid.UUID,
    session: AsyncSession = Depends(get_control_db),
    user: User = Depends(get_current_verified_user),
) -> ConversationFeatureSummary:
    from sqlalchemy.dialects.postgresql import insert
    from .models import ChatMessageReceipt

    member = await _member(
        session,
        conversation_id,
        user.id,
    )

    await session.scalar(
        select(ConversationMember.id)
        .where(ConversationMember.id == member.id)
        .with_for_update()
    )

    message = await _message(
        session,
        conversation_id,
        message_id,
    )

    if message.deleted_at is not None:
        raise HTTPException(
            status_code=404,
            detail="Message not found.",
        )

    pref = await session.scalar(
        select(ChatConversationPreference).where(
            ChatConversationPreference.conversation_id
            == conversation_id,
            ChatConversationPreference.user_id == user.id,
        )
    )

    advanced = (
        pref is None
        or pref.last_read_at is None
        or pref.last_read_at < message.created_at
    )

    statement = insert(
        ChatConversationPreference,
    ).values(
        id=uuid.uuid4(),
        conversation_id=conversation_id,
        user_id=user.id,
        last_read_at=message.created_at,
    )

    await session.execute(
        statement.on_conflict_do_update(
            index_elements=[
                "conversation_id",
                "user_id",
            ],
            set_={
                "last_read_at": func.greatest(
                    ChatConversationPreference.last_read_at,
                    statement.excluded.last_read_at,
                ),
            },
        )
    )

    # Record only this authenticated reader. Keep the first read time.
    unread_ids = list(
        await session.scalars(
            select(ChatMessage.id)
            .outerjoin(
                ChatMessageReceipt,
                (
                    ChatMessageReceipt.message_id
                    == ChatMessage.id
                )
                & (
                    ChatMessageReceipt.user_id
                    == user.id
                ),
            )
            .where(
                ChatMessage.conversation_id
                == conversation_id,
                ChatMessage.sender_user_id != user.id,
                ChatMessage.deleted_at.is_(None),
                ChatMessage.created_at
                <= message.created_at,
                ChatMessageReceipt.id.is_(None),
            )
        )
    )

    now = datetime.now(timezone.utc)

    for start in range(0, len(unread_ids), 400):
        ids = unread_ids[start:start + 400]

        receipts = [
            {
                "id": uuid.uuid4(),
                "message_id": item,
                "user_id": user.id,
                "read_at": now,
            }
            for item in ids
        ]

        await session.execute(
            insert(ChatMessageReceipt)
            .values(receipts)
            .on_conflict_do_nothing(
                index_elements=[
                    "message_id",
                    "user_id",
                ],
            )
        )

        deliveries = [
            {
                "id": uuid.uuid4(),
                "message_id": item,
                "user_id": user.id,
                "delivered_at": now,
                "read_at": now,
            }
            for item in ids
        ]

        delivery = insert(
            ChatMessageDelivery,
        ).values(deliveries)

        await session.execute(
            delivery.on_conflict_do_update(
                index_elements=[
                    "message_id",
                    "user_id",
                ],
                set_={
                    "read_at": func.coalesce(
                        ChatMessageDelivery.read_at,
                        now,
                    ),
                },
            )
        )

    await session.commit()

    if advanced or unread_ids:
        await _event(
            ChatRealtimeEventType.MESSAGE_READ,
            conversation_id,
            user.id,
            {
                "message_id": str(message_id),
                "user_id": str(user.id),
                "read_at": now.isoformat(),
            },
        )

    if pref is not None:
        await session.refresh(pref)

    return await _summary(
        session,
        conversation_id,
        user.id,
    )


@router.post(
    "/{conversation_id}/messages/{message_id}/reactions/toggle",
    response_model=FeatureMessagePublic,
)
async def toggle_reaction(
    conversation_id: uuid.UUID,
    message_id: uuid.UUID,
    request: ReactionRequest,
    session: AsyncSession = Depends(get_control_db),
    user: User = Depends(get_current_verified_user),
) -> FeatureMessagePublic:
    await _member(
        session,
        conversation_id,
        user.id,
    )

    message = await session.scalar(
        select(ChatMessage)
        .where(
            ChatMessage.id == message_id,
            ChatMessage.conversation_id == conversation_id,
            ChatMessage.deleted_at.is_(None),
        )
        .with_for_update()
    )

    if message is None:
        raise HTTPException(
            status_code=404,
            detail="Message not found.",
        )

    existing = await session.scalar(
        select(ChatMessageReaction).where(
            ChatMessageReaction.message_id == message_id,
            ChatMessageReaction.user_id == user.id,
            ChatMessageReaction.emoji == request.emoji,
        )
    )

    if existing is not None:
        await session.delete(existing)
        action = "remove"
    else:
        session.add(
            ChatMessageReaction(
                message_id=message_id,
                user_id=user.id,
                emoji=request.emoji,
            )
        )
        action = "add"

    await session.commit()
    await session.refresh(message)

    await _event(
        ChatRealtimeEventType.MESSAGE_REACTION,
        conversation_id,
        user.id,
        {
            "message_id": str(message_id),
            "emoji": request.emoji,
            "action": action,
        },
    )

    return await _enrich(
        session,
        message,
        user.id,
    )

@router.get(
    "/{conversation_id}/messages/{message_id}/reactions"
)
async def conversation_message_reaction_people(
    conversation_id: uuid.UUID,
    message_id: uuid.UUID,
    session: AsyncSession = Depends(get_control_db),
    user: User = Depends(get_current_verified_user),
):
    await _member(
        session,
        conversation_id,
        user.id,
    )

    message = await _message(
        session,
        conversation_id,
        message_id,
    )

    if message.deleted_at is not None:
        raise HTTPException(
            status_code=404,
            detail="Message not found.",
        )

    result = await session.execute(
        select(
            ChatMessageReaction,
            User,
        )
        .join(
            User,
            User.id == ChatMessageReaction.user_id,
        )
        .where(
            ChatMessageReaction.message_id == message_id,
        )
        .order_by(
            ChatMessageReaction.emoji,
            User.id,
        )
    )

    rows = result.all()

    return {
        "message_id": str(message_id),
        "counts": dict(
            Counter(
                reaction.emoji
                for reaction, _ in rows
            )
        ),
        "items": [
            {
                "user_id": str(reaction.user_id),
                "emoji": reaction.emoji,
                "mine": reaction.user_id == user.id,
                "name": (
                    getattr(person, "name", None)
                    or getattr(person, "full_name", None)
                ),
                "username": getattr(
                    person,
                    "username",
                    None,
                ),
                "avatar_url": getattr(
                    person,
                    "avatar_url",
                    None,
                ),
            }
            for reaction, person in rows
        ],
    }

__all__ = ["router"]
