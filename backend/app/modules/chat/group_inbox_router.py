"""Group-inbox actions. Personal clearing never deletes shared messages.

Mount this router inside app.modules.chat.router (which already prefixes /chat).
Run backend/scripts/ensure_group_inbox_state.py once before serving requests.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, MetaData, Table, func, select, update
from sqlalchemy.dialects.postgresql import UUID, insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_control_db
from app.modules.auth.models import User
from app.modules.auth.permissions import get_current_verified_user
from .features_models import ChatConversationPreference
from .models import Conversation, ConversationMember

router = APIRouter(prefix="/group-inbox", tags=["Group inbox"])

# This small additive table intentionally does not change existing ORM classes.
group_inbox_state = Table(
    "chat_group_inbox_state",
    MetaData(),
    Column("conversation_id", UUID(as_uuid=True), primary_key=True),
    Column("user_id", UUID(as_uuid=True), primary_key=True),
    Column("cleared_before", DateTime(timezone=True), nullable=False),
)


class GroupInboxState(BaseModel):
    conversation_id: uuid.UUID
    cleared_before: datetime | None = None


def _enum_value(value: object) -> str:
    return str(getattr(value, "value", value)).lower()


async def _active_group_member(
    session: AsyncSession,
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
    *,
    lock: bool = False,
) -> tuple[Conversation, ConversationMember]:
    group_query = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.is_active.is_(True),
    )
    if lock:
        group_query = group_query.with_for_update()
    group = await session.scalar(group_query)
    if group is None or _enum_value(group.conversation_type) != "group":
        raise HTTPException(status_code=404, detail="Active group not found.")

    member_query = select(ConversationMember).where(
        ConversationMember.conversation_id == conversation_id,
        ConversationMember.user_id == user_id,
        ConversationMember.left_at.is_(None),
    )
    if lock:
        member_query = member_query.with_for_update()
    member = await session.scalar(member_query)
    if member is None:
        raise HTTPException(status_code=403, detail="You are not an active group member.")
    return group, member


@router.get("/states", response_model=list[GroupInboxState])
async def list_group_inbox_states(
    session: AsyncSession = Depends(get_control_db),
    user: User = Depends(get_current_verified_user),
) -> list[GroupInboxState]:
    rows = (await session.execute(
        select(group_inbox_state.c.conversation_id, group_inbox_state.c.cleared_before)
        .join(Conversation, Conversation.id == group_inbox_state.c.conversation_id)
        .join(ConversationMember,
              ConversationMember.conversation_id == group_inbox_state.c.conversation_id)
        .where(
            group_inbox_state.c.user_id == user.id,
            ConversationMember.user_id == user.id,
            ConversationMember.left_at.is_(None),
            Conversation.is_active.is_(True),
        )
    )).mappings()
    return [GroupInboxState(**dict(row)) for row in rows]


@router.get("/{conversation_id}/state", response_model=GroupInboxState)
async def get_group_inbox_state(
    conversation_id: uuid.UUID,
    session: AsyncSession = Depends(get_control_db),
    user: User = Depends(get_current_verified_user),
) -> GroupInboxState:
    await _active_group_member(session, conversation_id, user.id)
    cutoff = await session.scalar(
        select(group_inbox_state.c.cleared_before).where(
            group_inbox_state.c.conversation_id == conversation_id,
            group_inbox_state.c.user_id == user.id,
        )
    )
    return GroupInboxState(conversation_id=conversation_id, cleared_before=cutoff)


@router.post("/{conversation_id}/clear", response_model=GroupInboxState)
async def clear_group_chat_for_me(
    conversation_id: uuid.UUID,
    session: AsyncSession = Depends(get_control_db),
    user: User = Depends(get_current_verified_user),
) -> GroupInboxState:
    await _active_group_member(session, conversation_id, user.id, lock=True)
    cutoff = await session.scalar(select(func.clock_timestamp()))
    if cutoff is None:
        raise HTTPException(status_code=500, detail="Could not determine clear time.")
    # Preserve the newest clear watermark if requests arrive out of order.
    statement = insert(group_inbox_state).values(
        conversation_id=conversation_id, user_id=user.id, cleared_before=cutoff,
    )
    statement = statement.on_conflict_do_update(
        index_elements=[group_inbox_state.c.conversation_id, group_inbox_state.c.user_id],
        set_={"cleared_before": func.greatest(
            group_inbox_state.c.cleared_before, statement.excluded.cleared_before,
        )},
    ).returning(group_inbox_state.c.cleared_before)
    saved_cutoff = await session.scalar(statement)
    if saved_cutoff is None:
        raise HTTPException(status_code=500, detail="Could not save the personal clear time.")
    # Clearing a personal inbox also clears its old unread badge; it does not
    # fabricate message-view receipts or mark another member's messages deleted.
    preference = await session.scalar(select(ChatConversationPreference).where(
        ChatConversationPreference.conversation_id == conversation_id,
        ChatConversationPreference.user_id == user.id,
    ))
    if preference is None:
        preference = ChatConversationPreference(
            conversation_id=conversation_id, user_id=user.id, last_read_at=saved_cutoff,
        )
        session.add(preference)
    elif preference.last_read_at is None or preference.last_read_at < saved_cutoff:
        preference.last_read_at = saved_cutoff
    await session.commit()
    return GroupInboxState(conversation_id=conversation_id, cleared_before=saved_cutoff)


@router.delete("/{conversation_id}", status_code=204)
async def delete_group_for_everyone(
    conversation_id: uuid.UUID,
    session: AsyncSession = Depends(get_control_db),
    user: User = Depends(get_current_verified_user),
) -> Response:
    group, _ = await _active_group_member(session, conversation_id, user.id, lock=True)
    if group.created_by_user_id != user.id:
        raise HTTPException(status_code=403, detail="Only the group creator can delete this group.")
    now = await session.scalar(select(func.clock_timestamp()))
    group.is_active = False
    group.updated_at = now
    # End memberships too, so routes that check membership cannot keep sending
    # to this inactive group. Shared messages/files are retained in the database.
    await session.execute(update(ConversationMember).where(
        ConversationMember.conversation_id == conversation_id,
        ConversationMember.left_at.is_(None),
    ).values(left_at=now))
    await session.commit()
    return Response(status_code=204)


__all__ = ["router"]
