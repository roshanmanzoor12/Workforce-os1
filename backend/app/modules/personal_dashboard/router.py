from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, Field
from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_control_db
from app.core.logging import get_logger
from app.modules.auth.models import User
from app.modules.auth.permissions import get_current_verified_user
from app.modules.calls.enums import CallScope
from app.modules.calls.models import RealtimeCall, RealtimeCallParticipant
from app.modules.chat.enums import PresenceStatus
from app.modules.chat.models import ChatMessage, ChatPresence, Conversation, ConversationMember
from app.modules.friends.enums import FriendshipStatus
from app.modules.friends.models import Friendship

router = APIRouter(prefix="/personal/dashboard", tags=["Personal dashboard"])
logger = get_logger(__name__)


class FriendSummary(BaseModel):
    user_id: uuid.UUID
    name: str
    online: bool


class ConversationSummary(BaseModel):
    id: uuid.UUID
    name: str
    kind: str
    updated_at: datetime


class CallSummary(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    kind: str
    status: str
    created_at: datetime


class DashboardResponse(BaseModel):
    generated_at: datetime
    friends_total: int | None = None
    online_total: int | None = None
    incoming_requests: int | None = None
    conversations_total: int | None = None
    calls_total: int | None = None
    friends: list[FriendSummary] = Field(default_factory=list)
    conversations: list[ConversationSummary] = Field(default_factory=list)
    calls: list[CallSummary] = Field(default_factory=list)
    errors: dict[str, str] = Field(default_factory=dict)


def enum_value(value: object) -> str:
    return str(getattr(value, "value", value))


def friend_queries(user_id: uuid.UUID, now: datetime):
    own = or_(Friendship.user_low_id == user_id, Friendship.user_high_id == user_id)
    other_id = case(
        (Friendship.user_low_id == user_id, Friendship.user_high_id),
        else_=Friendship.user_low_id,
    )
    online = (
        (ChatPresence.status == PresenceStatus.ONLINE)
        & (ChatPresence.last_seen_at >= now - timedelta(seconds=120))
    )
    accepted = (
        select(User, online.label("online"))
        .select_from(Friendship)
        .join(User, User.id == other_id)
        .outerjoin(ChatPresence, ChatPresence.user_id == User.id)
        .where(own, Friendship.status == FriendshipStatus.ACCEPTED)
    )
    pending = select(func.count()).select_from(Friendship).where(
        own,
        Friendship.status == FriendshipStatus.PENDING,
        Friendship.requested_by_user_id != user_id,
    )
    return accepted, pending


def conversation_query(user_id: uuid.UUID):
    last_message_at = select(func.max(ChatMessage.created_at)).where(
        ChatMessage.conversation_id == Conversation.id,
        ChatMessage.deleted_at.is_(None),
    ).correlate(Conversation).scalar_subquery()
    recent_at = func.coalesce(last_message_at, Conversation.updated_at).label("recent_at")
    return (
        select(Conversation, recent_at)
        .join(ConversationMember, ConversationMember.conversation_id == Conversation.id)
        .where(
            ConversationMember.user_id == user_id,
            ConversationMember.left_at.is_(None),
            Conversation.is_active.is_(True),
        )
    )


def call_query(user_id: uuid.UUID):
    participant = select(RealtimeCallParticipant.id).where(
        RealtimeCallParticipant.call_id == RealtimeCall.id,
        RealtimeCallParticipant.user_id == user_id,
    ).exists()
    membership = select(ConversationMember.id).where(
        ConversationMember.conversation_id == RealtimeCall.conversation_id,
        ConversationMember.user_id == user_id,
        ConversationMember.left_at.is_(None),
    ).exists()
    return select(RealtimeCall).where(
        RealtimeCall.scope == CallScope.CONVERSATION,
        membership,
        or_(RealtimeCall.started_by_user_id == user_id, participant),
    )


@router.get("", response_model=DashboardResponse)
async def get_personal_dashboard(
    response: Response,
    session: AsyncSession = Depends(get_control_db),
    current_user: User = Depends(get_current_verified_user),
) -> DashboardResponse:
    response.headers["Cache-Control"] = "private, no-store"
    now = datetime.now(timezone.utc)
    user_id = current_user.id
    result = DashboardResponse(generated_at=now)

    # A savepoint keeps a failed optional section from poisoning later queries.
    try:
        async with session.begin_nested():
            accepted, pending = friend_queries(user_id, now)
            accepted_rows = accepted.subquery()
            total = await session.scalar(select(func.count()).select_from(accepted_rows))
            online_total = await session.scalar(
                select(func.count()).select_from(accepted_rows).where(accepted_rows.c.online.is_(True))
            )
            incoming = await session.scalar(pending)
            rows = (await session.execute(
                accepted.order_by(online_total_expression(now).desc().nullslast(), User.username, User.id).limit(8)
            )).all()
            friends = [FriendSummary(
                user_id=user.id,
                name=" ".join(filter(None, [user.first_name, user.last_name])) or user.username,
                online=bool(is_online),
            ) for user, is_online in rows]
        result.friends_total = int(total or 0)
        result.online_total = int(online_total or 0)
        result.incoming_requests = int(incoming or 0)
        result.friends = friends
    except Exception as exc:
        logger.error("personal_dashboard_section_failed", section="friends", failure_type=type(exc).__name__)
        result.errors["friends"] = "Friends could not be loaded. Please retry."

    try:
        async with session.begin_nested():
            query = conversation_query(user_id)
            total = await session.scalar(select(func.count()).select_from(query.subquery()))
            rows = (await session.execute(
                query.order_by(query.selected_columns.recent_at.desc(), Conversation.id.desc()).limit(8)
            )).all()
            other_ids = {
                item.direct_user_high_id if item.direct_user_low_id == user_id else item.direct_user_low_id
                for item, _ in rows if enum_value(item.conversation_type) == "direct"
            }
            people = (await session.scalars(select(User).where(User.id.in_(other_ids)))).all() if other_ids else []
            names = {p.id: " ".join(filter(None, [p.first_name, p.last_name])) or p.username for p in people}
            conversations = []
            for item, recent_at in rows:
                other_id = item.direct_user_high_id if item.direct_user_low_id == user_id else item.direct_user_low_id
                conversations.append(ConversationSummary(
                    id=item.id,
                    name=item.name or names.get(other_id, "Direct conversation"),
                    kind=enum_value(item.conversation_type),
                    updated_at=recent_at,
                ))
        result.conversations_total = int(total or 0)
        result.conversations = conversations
    except Exception as exc:
        logger.error("personal_dashboard_section_failed", section="conversations", failure_type=type(exc).__name__)
        result.errors["conversations"] = "Conversations could not be loaded. Please retry."

    try:
        async with session.begin_nested():
            query = call_query(user_id)
            total = await session.scalar(select(func.count()).select_from(query.subquery()))
            rows = (await session.scalars(
                query.order_by(RealtimeCall.created_at.desc(), RealtimeCall.id.desc()).limit(8)
            )).all()
            calls = [CallSummary(
                id=item.id,
                conversation_id=item.conversation_id,
                kind=enum_value(item.kind),
                status=enum_value(item.status),
                created_at=item.created_at,
            ) for item in rows]
        result.calls_total = int(total or 0)
        result.calls = calls
    except Exception as exc:
        logger.error("personal_dashboard_section_failed", section="calls", failure_type=type(exc).__name__)
        result.errors["calls"] = "Call history could not be loaded. Please retry."

    return result


def online_total_expression(now: datetime):
    return (
        (ChatPresence.status == PresenceStatus.ONLINE)
        & (ChatPresence.last_seen_at >= now - timedelta(seconds=120))
    )