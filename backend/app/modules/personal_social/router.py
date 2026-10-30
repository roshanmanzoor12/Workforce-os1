from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_control_db
from app.modules.auth.models import User
from app.modules.auth.permissions import get_current_verified_user
from app.modules.chat.enums import ConversationType
from app.modules.chat.models import ChatPresence, Conversation, ConversationMember
from app.modules.chat.schemas import ConversationPublic
from app.modules.friends.enums import FriendshipStatus
from app.modules.friends.models import Friendship
from app.modules.friends.schemas import FriendshipPublic
from app.modules.friends.service import FriendshipService
from app.modules.friends.router import translate_friendship_error

router = APIRouter(prefix="/personal/social", tags=["Personal social"])


class RequestInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    identifier: str = Field(min_length=3, max_length=64)


def person(user: User) -> dict:
    return {
        "id": str(user.id), "username": user.username,
        "name": " ".join(filter(None, [user.first_name, user.last_name])) or user.username,
        "avatar_url": user.avatar_url,
    }


async def own_relationships(db: AsyncSession, user_id: uuid.UUID):
    return list((await db.execute(select(Friendship).where(or_(
        Friendship.user_low_id == user_id, Friendship.user_high_id == user_id,
    )).order_by(Friendship.updated_at.desc()))).scalars().all())


def peer(row: Friendship, user_id: uuid.UUID):
    return row.user_high_id if row.user_low_id == user_id else row.user_low_id


async def resolve_person(db: AsyncSession, identifier: str, current_id: uuid.UUID):
    value = identifier.strip().removeprefix("@").lower()
    try:
        condition = User.id == uuid.UUID(value)
    except ValueError:
        condition = func.lower(User.username) == value
    target = (await db.execute(select(User).where(
        condition, User.is_active.is_(True), User.is_locked.is_(False),
        User.is_email_verified.is_(True), User.id != current_id,
    ))).scalar_one_or_none()
    if target is None:
        raise HTTPException(404, "No eligible user found. Use their exact username or User ID.")
    return target


@router.get("/people")
async def lookup_person(
    response: Response, query: str = Query(min_length=3, max_length=64),
    db: AsyncSession = Depends(get_control_db),
    user: User = Depends(get_current_verified_user),
):
    response.headers["Cache-Control"] = "private, no-store"
    target = await resolve_person(db, query, user.id)
    return person(target)


@router.get("/friends")
async def friends(
    response: Response, db: AsyncSession = Depends(get_control_db),
    user: User = Depends(get_current_verified_user),
):
    response.headers["Cache-Control"] = "private, no-store"
    rows = await own_relationships(db, user.id)
    ids = [peer(row, user.id) for row in rows]
    people = {item.id: item for item in (await db.execute(
        select(User).where(User.id.in_(ids))
    )).scalars().all()} if ids else {}
    presences = {item.user_id: item for item in (await db.execute(
        select(ChatPresence).where(ChatPresence.user_id.in_(ids))
    )).scalars().all()} if ids else {}
    items = []
    now = datetime.now(timezone.utc)
    for row in rows:
        target_id = peer(row, user.id)
        target = people.get(target_id)
        if target is None:
            continue
        presence = presences.get(target_id)
        fresh = False
        if presence is not None:
            last_seen = presence.last_seen_at
            if last_seen.tzinfo is None:
                last_seen = last_seen.replace(tzinfo=timezone.utc)
            fresh = 0 <= (now - last_seen).total_seconds() <= 120
        items.append({
            **FriendshipPublic.model_validate(row).model_dump(mode="json"),
            "person": person(target),
            "direction": "outgoing" if row.requested_by_user_id == user.id else "incoming",
            "blocked_by_me": row.status == FriendshipStatus.BLOCKED and row.requested_by_user_id == user.id,
            "presence": presence.status.value if fresh and row.status == FriendshipStatus.ACCEPTED else "offline",
        })
    return {"items": items}


@router.post("/requests", status_code=201)
async def send_request(
    payload: RequestInput, db: AsyncSession = Depends(get_control_db),
    user: User = Depends(get_current_verified_user),
):
    target = await resolve_person(db, payload.identifier, user.id)
    try:
        row = await FriendshipService(db).send_request(
            requester_user_id=user.id, target_user_id=target.id,
        )
        result = FriendshipPublic.model_validate(row).model_dump(mode="json")
        await db.commit()
        return result
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(409, "Relationship changed. Refresh and try again.") from exc
    except ValueError as exc:
        await db.rollback()
        raise translate_friendship_error(exc) from exc


@router.post("/friends/{relationship_id}/{action}")
async def friend_action(
    relationship_id: uuid.UUID,
    action: Literal["accept", "reject", "cancel", "remove", "block", "unblock"],
    db: AsyncSession = Depends(get_control_db),
    user: User = Depends(get_current_verified_user),
):
    row = (await db.execute(select(Friendship).where(
        Friendship.id == relationship_id,
        or_(Friendship.user_low_id == user.id, Friendship.user_high_id == user.id),
    ).with_for_update())).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "Relationship not found.")
    outgoing = row.requested_by_user_id == user.id
    pending = row.status == FriendshipStatus.PENDING
    if action == "accept":
        if not pending or outgoing:
            raise HTTPException(409, "Only an incoming pending request can be accepted.")
        row.status = FriendshipStatus.ACCEPTED
        row.accepted_at = datetime.now(timezone.utc)
    elif action in {"reject", "cancel"}:
        if not pending or (action == "cancel") != outgoing:
            raise HTTPException(409, "This request cannot be changed using that action.")
        await db.delete(row)
    elif action == "remove":
        if row.status != FriendshipStatus.ACCEPTED:
            raise HTTPException(409, "Only an accepted friend can be removed.")
        await db.delete(row)
    elif action == "block":
        if row.status == FriendshipStatus.BLOCKED and not outgoing:
            raise HTTPException(403, "This relationship is already blocked.")
        row.status = FriendshipStatus.BLOCKED
        row.requested_by_user_id = user.id
        row.accepted_at = None
        row.blocked_at = datetime.now(timezone.utc)
    else:
        if row.status != FriendshipStatus.BLOCKED or not outgoing:
            raise HTTPException(403, "Only the blocking user can remove this block.")
        await db.delete(row)
    await db.commit()
    return {"success": True}


@router.get("/conversations")
async def conversations(
    response: Response, db: AsyncSession = Depends(get_control_db),
    user: User = Depends(get_current_verified_user),
):
    response.headers["Cache-Control"] = "private, no-store"
    rows = list((await db.execute(select(Conversation).join(ConversationMember).where(
        ConversationMember.user_id == user.id, ConversationMember.left_at.is_(None),
        Conversation.is_active.is_(True),
    ).order_by(Conversation.updated_at.desc()))).scalars().all())
    ids = [row.id for row in rows]
    members = (await db.execute(select(ConversationMember, User).join(
        User, User.id == ConversationMember.user_id,
    ).where(ConversationMember.conversation_id.in_(ids), ConversationMember.left_at.is_(None)))).all() if ids else []
    grouped: dict = {}
    for member, member_user in members:
        grouped.setdefault(member.conversation_id, []).append({
            **person(member_user), "role": member.role.value,
        })
    accepted = {peer(row, user.id) for row in await own_relationships(db, user.id)
                if row.status == FriendshipStatus.ACCEPTED}
    result = []
    for row in rows:
        direct = row.conversation_type == ConversationType.DIRECT
        target = row.direct_user_high_id if row.direct_user_low_id == user.id else row.direct_user_low_id
        result.append({
            **ConversationPublic.model_validate(row).model_dump(mode="json"),
            "members": grouped.get(row.id, []),
            "can_message": not direct or target in accepted,
        })
    return result


@router.get("/conversations/{conversation_id}/messages")
async def message_page(
    conversation_id: uuid.UUID, response: Response,
    cursor: str | None = None, limit: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_control_db),
    user: User = Depends(get_current_verified_user),
):
    from sqlalchemy import and_
    from app.modules.chat.models import ChatMessage
    from app.modules.chat.pagination import decode_message_cursor, encode_message_cursor
    from app.modules.chat.schemas import ChatMessagePublic
    allowed = (await db.execute(select(ConversationMember).join(Conversation).where(
        ConversationMember.conversation_id == conversation_id,
        ConversationMember.user_id == user.id, ConversationMember.left_at.is_(None),
        Conversation.is_active.is_(True),
    ))).scalar_one_or_none()
    if allowed is None:
        raise HTTPException(404, "Conversation not found.")
    query = select(ChatMessage).where(ChatMessage.conversation_id == conversation_id)
    if cursor:
        try:
            before = decode_message_cursor(cursor)
        except ValueError as exc:
            raise HTTPException(400, "Invalid message cursor.") from exc
        query = query.where(or_(ChatMessage.created_at < before.created_at, and_(
            ChatMessage.created_at == before.created_at, ChatMessage.id < before.message_id,
        )))
    rows = list((await db.execute(query.order_by(
        ChatMessage.created_at.desc(), ChatMessage.id.desc(),
    ).limit(limit + 1))).scalars().all())
    more = len(rows) > limit
    rows = rows[:limit]
    next_cursor = None
    if more:
        stamp = rows[-1].created_at
        if stamp.tzinfo is None:
            stamp = stamp.replace(tzinfo=timezone.utc)
        next_cursor = encode_message_cursor(created_at=stamp, message_id=rows[-1].id)
    items = []
    for row in rows:
        item = ChatMessagePublic.model_validate(row).model_dump(mode="json")
        if row.deleted_at is not None:
            item["content"] = ""
        items.append(item)
    response.headers["Cache-Control"] = "private, no-store"
    return {
        "items": items,
        "has_more": more,
        "next_cursor": next_cursor,
    }