
from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy import (
    Column, MetaData, String, Table, and_, case, func, or_, select,
)
from sqlalchemy.dialects.postgresql import UUID, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.core.database import get_control_db
from app.modules.auth.models import User
from app.modules.auth.permissions import get_current_verified_user
from app.modules.chat.enums import ConversationType
from app.modules.chat.models import Conversation, ConversationMember
from app.modules.chat.service import ChatService, ChatError

from .delivery_router import display_name
from .enums import (
    CallKind, CallParticipantState, CallScope, CallStatus, ScreenShareState,
)
from .models import RealtimeCall, RealtimeCallParticipant
from .schemas import (
    CallParticipantResponse, CallResponse, CreateCallRequest,
)
from .service import CallService


def no_store(response: Response):
    response.headers["Cache-Control"] = "private, no-store"


router = APIRouter(dependencies=[Depends(no_store)])
metadata = MetaData()

numbers = Table(
    "personal_call_numbers_v1",
    metadata,
    Column("user_id", UUID(as_uuid=True), primary_key=True),
    Column("calling_number", String(10), nullable=False, unique=True),
)

favorites = Table(
    "personal_call_favorites_v1",
    metadata,
    Column("owner_id", UUID(as_uuid=True), primary_key=True),
    Column("target_id", UUID(as_uuid=True), primary_key=True),
)


async def calling_number(
    session: AsyncSession,
    user_id: uuid.UUID,
) -> str:
    for _ in range(12):
        existing = await session.scalar(
            select(numbers.c.calling_number).where(
                numbers.c.user_id == user_id,
            )
        )

        if existing is not None:
            return existing

        value = str(
            1_000_000_000 + secrets.randbelow(9_000_000_000)
        )

        await session.execute(
            insert(numbers)
            .values(user_id=user_id, calling_number=value)
            .on_conflict_do_nothing()
        )

    raise HTTPException(
        503,
        "Could not allocate a calling number. Please retry.",
    )


async def person_public(
    session: AsyncSession,
    person: User,
) -> dict:
    return {
        "user_id": str(person.id),
        "name": display_name(person),
        "username": person.username,
        "avatar_url": person.avatar_url,
        "calling_number": await calling_number(session, person.id),
    }


def contact_ids(owner: uuid.UUID):
    mine = aliased(ConversationMember)

    return (
        select(ConversationMember.user_id)
        .join(
            mine,
            mine.conversation_id == ConversationMember.conversation_id,
        )
        .join(
            Conversation,
            Conversation.id == ConversationMember.conversation_id,
        )
        .where(
            mine.user_id == owner,
            mine.left_at.is_(None),
            ConversationMember.left_at.is_(None),
            Conversation.is_active.is_(True),
            ConversationMember.user_id != owner,
        )
        .distinct()
    )


@router.get("/numbers/me")
async def my_number(
    session: AsyncSession = Depends(get_control_db),
    user: User = Depends(get_current_verified_user),
):
    result = await person_public(session, user)
    await session.commit()
    return result


@router.get("/numbers/lookup")
async def lookup_number(
    number: str = Query(pattern=r"^[0-9]{10}$"),
    session: AsyncSession = Depends(get_control_db),
    user: User = Depends(get_current_verified_user),
):
    person = await session.scalar(
        select(User)
        .join(numbers, numbers.c.user_id == User.id)
        .where(
            numbers.c.calling_number == number,
            User.is_active.is_(True),
            User.is_email_verified.is_(True),
            User.is_locked.is_(False),
        )
    )

    if person is None:
        raise HTTPException(
            404,
            "No available account has this calling number.",
        )

    return await person_public(session, person)


@router.get("/contacts")
async def list_contacts(
    session: AsyncSession = Depends(get_control_db),
    user: User = Depends(get_current_verified_user),
):
    people = list(
        await session.scalars(
            select(User)
            .where(
                User.id.in_(contact_ids(user.id)),
                User.is_active.is_(True),
            )
            .order_by(User.username)
        )
    )

    items = [
        await person_public(session, person)
        for person in people
    ]

    await session.commit()
    return {"items": items}


@router.get("/favorites")
async def list_favorites(
    session: AsyncSession = Depends(get_control_db),
    user: User = Depends(get_current_verified_user),
):
    ids = list(
        await session.scalars(
            select(favorites.c.target_id).where(
                favorites.c.owner_id == user.id,
            )
        )
    )
    return {"user_ids": [str(item) for item in ids]}


@router.put("/favorites/{target_id}", status_code=204)
async def add_favorite(
    target_id: uuid.UUID,
    session: AsyncSession = Depends(get_control_db),
    user: User = Depends(get_current_verified_user),
):
    allowed = await session.scalar(
        contact_ids(user.id).where(
            ConversationMember.user_id == target_id,
        )
    )

    if allowed is None:
        raise HTTPException(
            403,
            "Choose a contact from one of your conversations.",
        )

    await session.execute(
        insert(favorites)
        .values(owner_id=user.id, target_id=target_id)
        .on_conflict_do_nothing()
    )
    await session.commit()
    return Response(status_code=204)


@router.delete("/favorites/{target_id}", status_code=204)
async def remove_favorite(
    target_id: uuid.UUID,
    session: AsyncSession = Depends(get_control_db),
    user: User = Depends(get_current_verified_user),
):
    await session.execute(
        favorites.delete().where(
            favorites.c.owner_id == user.id,
            favorites.c.target_id == target_id,
        )
    )
    await session.commit()
    return Response(status_code=204)


def missed_expression(viewer, owner):
    return and_(
        RealtimeCall.started_by_user_id != owner,
        viewer.joined_at.is_(None),
        or_(
            RealtimeCall.status.in_([
                CallStatus.ENDED,
                CallStatus.CANCELLED,
            ]),
            and_(
                RealtimeCall.status == CallStatus.RINGING,
                RealtimeCall.created_at <
                datetime.now(timezone.utc) - timedelta(seconds=40),
            ),
        ),
    )


async def call_public(
    session: AsyncSession,
    call: RealtimeCall,
    owner: uuid.UUID,
) -> dict:
    participants = list(
        await session.scalars(
            select(RealtimeCallParticipant)
            .where(RealtimeCallParticipant.call_id == call.id)
            .order_by(
                RealtimeCallParticipant.created_at,
                RealtimeCallParticipant.user_id,
            )
        )
    )

    viewer = next(
        (item for item in participants if item.user_id == owner),
        None,
    )

    if viewer is None:
        raise HTTPException(
            403,
            "You are not a participant in this call.",
        )

    people = {
        person.id: person
        for person in await session.scalars(
            select(User).where(
                User.id.in_([
                    item.user_id for item in participants
                ]),
            )
        )
    }

    outgoing = call.started_by_user_id == owner

    peer_id = (
        next(
            (
                item.user_id
                for item in participants
                if item.user_id != owner
            ),
            None,
        )
        if outgoing
        else call.started_by_user_id
    )

    peer = people.get(peer_id)
    caller = people.get(call.started_by_user_id)

    conversation = (
        await session.get(Conversation, call.conversation_id)
        if call.conversation_id
        else None
    )

    kind = (
        getattr(
            conversation.conversation_type,
            "value",
            conversation.conversation_type,
        )
        if conversation
        else "direct"
    )

    now = datetime.now(timezone.utc)
    stale = (
        call.status == CallStatus.RINGING
        and call.created_at < now - timedelta(seconds=40)
    )

    missed = (
        not outgoing
        and viewer.joined_at is None
        and (
            call.status in (
                CallStatus.ENDED,
                CallStatus.CANCELLED,
            )
            or stale
        )
    )

    outcome = (
        "Missed" if missed
        else "Active" if call.status == CallStatus.ACTIVE
        else "No answer" if stale
        else "Cancelled" if call.status == CallStatus.CANCELLED
        else "Completed" if call.status == CallStatus.ENDED
        else "Ringing"
    )

    if viewer.state == CallParticipantState.DECLINED:
        outcome = "Declined"

    result = CallResponse(
        id=call.id,
        scope=call.scope,
        conversation_id=call.conversation_id,
        channel_id=call.channel_id,
        started_by_user_id=call.started_by_user_id,
        kind=call.kind,
        status=call.status,
        created_at=call.created_at,
        started_at=call.started_at,
        ended_at=call.ended_at,
        participants=[
            CallParticipantResponse.model_validate(item)
            for item in participants
        ],
    ).model_dump(mode="json")

    result.update(
        contact_avatar_url=peer.avatar_url if peer else None,
        conversation_type=str(kind).lower(),
        conversation_name=(
            conversation.name or "Group call"
            if str(kind).lower() == "group"
            else display_name(peer) if peer else "Personal call"
        ),
        caller_name=(
            display_name(caller) if caller else "Caller"
        ),
        contact_number=(
            await calling_number(session, peer.id)
            if peer
            else None
        ),
        direction=(
            "Outgoing" if outgoing
            else "Missed" if missed
            else "Incoming"
        ),
        outcome=outcome,
        duration_seconds=(
            max(
                0,
                int(
                    (
                        (call.ended_at or now) - call.started_at
                    ).total_seconds()
                ),
            )
            if call.started_at
            else 0
        ),
    )

    return result


@router.get("/history")
async def history(
    direction: Literal[
        "all", "incoming", "outgoing", "missed"
    ] = "all",
    kind: Literal["VOICE", "VIDEO"] | None = None,
    search: str = Query(default="", max_length=120),
    group_only: bool = False,
    limit: int = Query(default=5, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_control_db),
    user: User = Depends(get_current_verified_user),
):
    owner = user.id
    viewer = aliased(RealtimeCallParticipant)
    peer = aliased(User)

    first_peer = (
        select(RealtimeCallParticipant.user_id)
        .where(
            RealtimeCallParticipant.call_id == RealtimeCall.id,
            RealtimeCallParticipant.user_id != owner,
        )
        .order_by(
            RealtimeCallParticipant.created_at,
            RealtimeCallParticipant.user_id,
        )
        .limit(1)
        .correlate(RealtimeCall)
        .scalar_subquery()
    )

    peer_id = case(
        (
            RealtimeCall.started_by_user_id != owner,
            RealtimeCall.started_by_user_id,
        ),
        else_=first_peer,
    )

    missed = missed_expression(viewer, owner)

    base = (
        select(RealtimeCall)
        .join(viewer, viewer.call_id == RealtimeCall.id)
        .outerjoin(
            Conversation,
            Conversation.id == RealtimeCall.conversation_id,
        )
        .outerjoin(peer, peer.id == peer_id)
        .where(
            viewer.user_id == owner,
            RealtimeCall.scope == CallScope.CONVERSATION,
        )
    )

    aggregate = base.with_only_columns(
        func.count(RealtimeCall.id),
        func.sum(case((missed, 1), else_=0)),
        func.sum(case(
            (RealtimeCall.kind == CallKind.VOICE, 1),
            else_=0,
        )),
        func.sum(case(
            (RealtimeCall.kind == CallKind.VIDEO, 1),
            else_=0,
        )),
        maintain_column_froms=True,
    )

    totals_row = (await session.execute(aggregate)).one()
    totals = {
        key: int(value or 0)
        for key, value in zip(
            ("total", "missed", "voice", "video"),
            totals_row,
        )
    }

    query = base

    if group_only:
        query = query.where(
            Conversation.conversation_type == ConversationType.GROUP,
        )

    if kind:
        query = query.where(
            RealtimeCall.kind == CallKind(kind),
        )

    if direction == "outgoing":
        query = query.where(
            RealtimeCall.started_by_user_id == owner,
        )
    elif direction == "incoming":
        query = query.where(
            RealtimeCall.started_by_user_id != owner,
        )
    elif direction == "missed":
        query = query.where(missed)

    if search.strip():
        term = "%" + search.strip() + "%"
        peer_numbers = select(numbers.c.user_id).where(
            numbers.c.calling_number.ilike(term),
        )
        query = query.where(or_(
            Conversation.name.ilike(term),
            peer.username.ilike(term),
            peer.first_name.ilike(term),
            peer.last_name.ilike(term),
            peer.id.in_(peer_numbers),
        ))

    total = int(
        await session.scalar(
            query.with_only_columns(
                func.count(RealtimeCall.id),
                maintain_column_froms=True,
            )
        )
        or 0
    )

    calls = list(
        await session.scalars(
            query.order_by(
                RealtimeCall.created_at.desc(),
                RealtimeCall.id.desc(),
            )
            .offset(offset)
            .limit(limit)
        )
    )

    items = [
        await call_public(session, call, owner)
        for call in calls
    ]

    await session.commit()

    return {
        "items": items,
        "total": total,
        "totals": totals,
    }


class DialRequest(BaseModel):
    number: str = Field(pattern=r"^[0-9]{10}$")
    kind: CallKind


@router.post("/dial", status_code=201)
async def dial(
    payload: DialRequest,
    session: AsyncSession = Depends(get_control_db),
    user: User = Depends(get_current_verified_user),
):
    owner = user.id

    target = await session.scalar(
        select(User)
        .join(numbers, numbers.c.user_id == User.id)
        .where(
            numbers.c.calling_number == payload.number,
            User.is_active.is_(True),
            User.is_email_verified.is_(True),
            User.is_locked.is_(False),
        )
    )

    if target is None:
        raise HTTPException(
            404,
            "No available account has this calling number.",
        )

    if target.id == owner:
        raise HTTPException(
            400,
            "You cannot call your own account.",
        )

    try:
        conversation = await ChatService(
            session,
        ).create_or_get_direct(
            current_user_id=owner,
            target_user_id=target.id,
        )
    except ChatError as exc:
        await session.rollback()
        raise HTTPException(403, str(exc)) from exc

    await session.flush()

    call = await CallService(session).create_call(
        user_id=owner,
        payload=CreateCallRequest(
            scope=CallScope.CONVERSATION,
            conversation_id=conversation.id,
            kind=payload.kind,
            invited_user_ids=[target.id],
        ),
    )

    result = await call_public(session, call, owner)
    await session.commit()
    return result


class InviteRequest(BaseModel):
    user_ids: list[uuid.UUID] = Field(
        min_length=1,
        max_length=99,
    )



@router.post("/{call_id}/participants/invite")
async def invite(
    call_id: uuid.UUID,
    payload: InviteRequest,
    session: AsyncSession = Depends(get_control_db),
    user: User = Depends(get_current_verified_user),
):
    from app.modules.friends.service import FriendshipService
    from .call_runtime import expire_call

    call = await session.scalar(
        select(RealtimeCall)
        .where(RealtimeCall.id == call_id)
        .with_for_update()
    )

    if call is None:
        raise HTTPException(404, "Call not found.")

    service = CallService(session)

    await service.assert_call_access(
        user_id=user.id,
        call=call,
    )

    await expire_call(session, call)

    if (
        call.scope != CallScope.CONVERSATION
        or call.status not in (
            CallStatus.RINGING,
            CallStatus.ACTIVE,
        )
    ):
        await session.commit()

        raise HTTPException(
            409,
            "Join an active personal call before inviting people.",
        )

    rows = list(
        await session.scalars(
            select(RealtimeCallParticipant).where(
                RealtimeCallParticipant.call_id == call_id,
            )
        )
    )

    if not any(
        row.user_id == user.id
        and row.state == CallParticipantState.JOINED
        for row in rows
    ):
        raise HTTPException(
            403,
            "Only joined participants can invite people.",
        )

    conversation = await session.get(
        Conversation,
        call.conversation_id,
    )

    if conversation is None or not conversation.is_active:
        raise HTTPException(404, "Conversation not found.")

    ids = set(payload.user_ids) - {user.id}

    if len({row.user_id for row in rows} | ids) > 100:
        raise HTTPException(
            400,
            "A call can contain at most 100 participants.",
        )

    for target in ids:
        if conversation.conversation_type == ConversationType.GROUP:
            await service.assert_target_access(
                user_id=target,
                scope=call.scope,
                conversation_id=call.conversation_id,
                channel_id=None,
            )
        elif not await FriendshipService(session).are_friends(
            first_user_id=user.id,
            second_user_id=target,
        ):
            raise HTTPException(
                403,
                "Call invitations require an accepted friendship.",
            )

        person = await session.get(User, target)

        if (
            person is None
            or not person.is_active
            or person.is_locked
            or not person.is_email_verified
        ):
            raise HTTPException(
                404,
                "That account is unavailable for calls.",
            )

    for target in ids:
        row = next(
            (
                row for row in rows
                if row.user_id == target
            ),
            None,
        )

        if row is None:
            session.add(
                RealtimeCallParticipant(
                    id=uuid.uuid4(),
                    call_id=call_id,
                    user_id=target,
                    state=CallParticipantState.INVITED,
                    microphone_enabled=True,
                    camera_enabled=False,
                    screen_share_state=ScreenShareState.STOPPED,
                )
            )

        elif row.state not in (
            CallParticipantState.JOINED,
            CallParticipantState.INVITED,
        ):
            row.state = CallParticipantState.INVITED
            row.left_at = None
            row.created_at = datetime.now(timezone.utc)

    await session.commit()

    return {
        "invited_user_ids": [
            str(value) for value in ids
        ],
    }

