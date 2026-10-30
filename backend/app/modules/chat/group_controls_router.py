from __future__ import annotations
from datetime import datetime, timezone
from collections import Counter
from sqlalchemy import case
import uuid
from typing import Literal
import asyncio
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_control_db
from app.modules.auth.models import User
from app.modules.auth.permissions import (
    get_current_verified_user,
)
from app.modules.attachments.models import (
    Attachment,
    AttachmentScope,
    AttachmentStatus,
)
from app.modules.attachments.binding_service import (
    AttachmentBindingService,
)
from app.modules.attachments.storage import (
    get_attachment_storage,
)

from .enums import (
    ConversationMemberRole as Role,
    ConversationType,
)
from .models import (
    Conversation,
    ConversationMember,
    ChatMessage,
)
from .schemas import ChatMessagePublic
from .features_router import _event
from .features_models import ChatMessageReaction
from .realtime_enums import ChatRealtimeEventType


router = APIRouter(
    prefix="/group-controls",
    tags=["Group controls"],
)


class GroupPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        min_length=1,
        max_length=120,
    )
    description: str = Field(
        default="",
        max_length=2000,
    )

    avatar_attachment_id: uuid.UUID | None = None
    avatar_mode: Literal["auto", "photo", "members"] | None = None

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError(
                "Group name cannot be empty."
            )

        return value.strip()


class RolePatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["admin", "member"]


class FileMessageCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    attachment_id: uuid.UUID


async def access(
    session: AsyncSession,
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
    *,
    lock: bool = False,
):
    statement = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.conversation_type
        == ConversationType.GROUP,
        Conversation.is_active.is_(True),
    )

    if lock:
        statement = statement.with_for_update()

    group = await session.scalar(statement)

    if group is None:
        raise HTTPException(
            404,
            "Group not found.",
        )

    member = await session.scalar(
        select(ConversationMember).where(
            ConversationMember.conversation_id
            == conversation_id,
            ConversationMember.user_id == user_id,
            ConversationMember.left_at.is_(None),
        )
    )

    if member is None:
        raise HTTPException(
            403,
            "You are not an active group member.",
        )

    return group, member


def manager(member: ConversationMember) -> None:
    if member.role not in (
        Role.OWNER,
        Role.ADMIN,
    ):
        raise HTTPException(
            403,
            "Only group owners and admins can manage this group.",
        )


def file_public(row: Attachment) -> dict:
    return (
        AttachmentBindingService.serialize(row)
        .model_dump(mode="json")
    )


@router.get("/{conversation_id}")
async def details(
    conversation_id: uuid.UUID,
    session: AsyncSession = Depends(get_control_db),
    user: User = Depends(get_current_verified_user),
):
    group, viewer = await access(
        session,
        conversation_id,
        user.id,
    )

    rows = (
        await session.execute(
            select(
                ConversationMember,
                User,
            )
            .join(
                User,
                User.id == ConversationMember.user_id,
            )
            .where(
                ConversationMember.conversation_id
                == conversation_id,
                ConversationMember.left_at.is_(None),
            )
            .order_by(
                ConversationMember.joined_at,
                ConversationMember.id,
            )
        )
    ).all()

    avatar_url = None

    if (
        group.avatar_attachment_id is not None
        and group.avatar_mode != "members"
    ):
        avatar_attachment = await session.scalar(
            select(Attachment).where(
                Attachment.id == group.avatar_attachment_id,
                Attachment.conversation_id == conversation_id,
                Attachment.scope == AttachmentScope.CONVERSATION,
                Attachment.status == AttachmentStatus.READY,
                Attachment.deleted_at.is_(None),
            )
        )

        if (
            avatar_attachment is not None
            and avatar_attachment.content_type.startswith("image/")
        ):
            object_key = avatar_attachment.object_key
            content_type = avatar_attachment.content_type

            avatar_url = await asyncio.to_thread(
                lambda: get_attachment_storage().create_download_url(
                    object_key=object_key,
                    expires_seconds=3600,
                    content_type=content_type,
                )
            )

    return {
        "current_user_id": str(user.id),
        "description": group.description,
        "avatar_url": avatar_url,
        "avatar_attachment_id": str(group.avatar_attachment_id) if group.avatar_attachment_id else None,
        "avatar_mode": group.avatar_mode,
        "can_manage": viewer.role
        in (
            Role.OWNER,
            Role.ADMIN,
        ),
        "members": [
            {
                "user_id": str(member.user_id),
                "role": member.role.value,
                "name": (
                    getattr(person, "name", None)
                    or getattr(
                        person,
                        "full_name",
                        None,
                    )
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
            for member, person in rows
        ],
    }


@router.patch("/{conversation_id}")
async def update_group(
    conversation_id: uuid.UUID,
    request: GroupPatch,
    session: AsyncSession = Depends(get_control_db),
    user: User = Depends(get_current_verified_user),
):
    group, member = await access(
        session,
        conversation_id,
        user.id,
        lock=True,
    )

    manager(member)

    attachment_id = (
        request.avatar_attachment_id
        if "avatar_attachment_id" in request.model_fields_set
        else group.avatar_attachment_id
    )
    mode = request.avatar_mode or group.avatar_mode or "auto"
    if mode == "photo" and attachment_id is None:
        raise HTTPException(422, "Upload a group photo before choosing photo mode.")
    if attachment_id is not None:
        attachment = await session.scalar(select(Attachment).where(
            Attachment.id == attachment_id,
            Attachment.conversation_id == conversation_id,
            Attachment.scope == AttachmentScope.CONVERSATION,
            Attachment.status == AttachmentStatus.READY,
            Attachment.deleted_at.is_(None),
            Attachment.message_id.is_not(None),
        ))
        if attachment is None:
            raise HTTPException(409, "The group photo must be a ready image shared in this group.")
        if attachment.content_type not in ("image/png", "image/jpeg", "image/webp", "image/gif"):
            raise HTTPException(422, "Choose a PNG, JPEG, WebP or GIF group photo.")
        if attachment.size_bytes > 2 * 1024 * 1024:
            raise HTTPException(422, "The group photo must be at most 2 MB.")
        if attachment_id != group.avatar_attachment_id and attachment.owner_user_id != user.id:
            raise HTTPException(403, "You can only choose your own new image uploads.")
        message = await session.get(ChatMessage, attachment.message_id)
        if message is None or message.deleted_at is not None or message.conversation_id != conversation_id:
            raise HTTPException(409, "The group photo's message is unavailable.")

    group.name = request.name
    group.description = request.description.strip()
    group.avatar_attachment_id = attachment_id
    group.avatar_mode = mode

    await session.commit()

    return {"ok": True}


@router.patch(
    "/{conversation_id}/members/{target_user_id}/role"
)
async def update_role(
    conversation_id: uuid.UUID,
    target_user_id: uuid.UUID,
    request: RolePatch,
    session: AsyncSession = Depends(get_control_db),
    user: User = Depends(get_current_verified_user),
):
    _, viewer = await access(
        session,
        conversation_id,
        user.id,
        lock=True,
    )

    if viewer.role != Role.OWNER:
        raise HTTPException(
            403,
            "Only the group owner can change admin roles.",
        )

    target = await session.scalar(
        select(ConversationMember)
        .where(
            ConversationMember.conversation_id
            == conversation_id,
            ConversationMember.user_id
            == target_user_id,
            ConversationMember.left_at.is_(None),
        )
        .with_for_update()
    )

    if target is None:
        raise HTTPException(
            404,
            "Member not found.",
        )

    if target.role == Role.OWNER:
        raise HTTPException(
            409,
            "The owner role cannot be changed here.",
        )

    target.role = Role(request.role)

    await session.commit()

    return {"ok": True}


@router.get("/{conversation_id}/files")
async def shared_files(
    conversation_id: uuid.UUID,
    limit: int = Query(
        100,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        0,
        ge=0,
    ),
    session: AsyncSession = Depends(get_control_db),
    user: User = Depends(get_current_verified_user),
):
    await access(
        session,
        conversation_id,
        user.id,
    )

    files = list(
        await session.scalars(
            select(Attachment)
            .join(
                ChatMessage,
                ChatMessage.id
                == Attachment.message_id,
            )
            .where(
                Attachment.conversation_id
                == conversation_id,
                Attachment.scope
                == AttachmentScope.CONVERSATION,
                Attachment.status
                == AttachmentStatus.READY,
                Attachment.deleted_at.is_(None),
                ChatMessage.conversation_id
                == conversation_id,
                ChatMessage.deleted_at.is_(None),
            )
            .order_by(
                Attachment.created_at,
                Attachment.id,
            )
            .offset(offset)
            .limit(limit)
        )
    )

    return [
        file_public(item)
        for item in files
    ]


@router.post(
    "/{conversation_id}/attachment-messages"
)
async def send_file(
    conversation_id: uuid.UUID,
    request: FileMessageCreate,
    session: AsyncSession = Depends(get_control_db),
    user: User = Depends(get_current_verified_user),
):
    await access(
        session,
        conversation_id,
        user.id,
    )

    binder = AttachmentBindingService(
        session=session,
        storage=get_attachment_storage(),
    )

    attachment = await session.scalar(
        select(Attachment)
        .where(
            Attachment.id == request.attachment_id,
        )
        .with_for_update()
    )

    if attachment is None:
        raise HTTPException(
            404,
            "Attachment not found.",
        )

    if attachment.owner_user_id != user.id:
        raise HTTPException(
            403,
            "You can only send your own uploads.",
        )

    if (
        attachment.scope
        != AttachmentScope.CONVERSATION
        or attachment.conversation_id
        != conversation_id
    ):
        raise HTTPException(
            409,
            "Attachment belongs to another conversation.",
        )

    if (
        attachment.status != AttachmentStatus.READY
        or attachment.deleted_at is not None
    ):
        raise HTTPException(
            409,
            "Upload is not ready.",
        )

    # Retrying with the same attachment does not create
    # a second message.
    if attachment.message_id is not None:
        message = await session.get(
            ChatMessage,
            attachment.message_id,
        )

        if (
            message is None
            or message.deleted_at is not None
            or message.conversation_id
            != conversation_id
        ):
            raise HTTPException(
                409,
                "Attachment message is unavailable.",
            )

        return {
            **ChatMessagePublic.model_validate(
                message
            ).model_dump(mode="json"),
            "attachments": [
                file_public(attachment),
            ],
        }

    message = ChatMessage(
        conversation_id=conversation_id,
        sender_user_id=user.id,
        content=attachment.original_filename,
    )

    try:
        session.add(message)

        await session.flush()

        message_id = message.id

        # The existing binding service commits the new
        # message and attachment binding together.
        await binder.bind_conversation(
            user_id=user.id,
            conversation_id=conversation_id,
            message_id=message_id,
            attachment_ids=[
                attachment.id,
            ],
        )

    except Exception:
        await session.rollback()
        raise

    await session.refresh(message)
    await session.refresh(attachment)

    await _event(
        ChatRealtimeEventType.MESSAGE_CREATED,
        conversation_id,
        user.id,
        {
            "message_id": str(message_id),
        },
    )

    return {
        **ChatMessagePublic.model_validate(
            message
        ).model_dump(mode="json"),
        "attachments": [
            file_public(attachment),
        ],
    }

@router.post("/{conversation_id}/leave")
async def leave_group(
    conversation_id: uuid.UUID,
    session: AsyncSession = Depends(get_control_db),
    user: User = Depends(get_current_verified_user),
):
    group, viewer = await access(
        session,
        conversation_id,
        user.id,
        lock=True,
    )

    remaining = list(
        await session.scalars(
            select(ConversationMember)
            .where(
                ConversationMember.conversation_id
                == conversation_id,
                ConversationMember.user_id != user.id,
                ConversationMember.left_at.is_(None),
            )
            .order_by(
                case(
                    (
                        ConversationMember.role == Role.ADMIN,
                        0,
                    ),
                    else_=1,
                ),
                ConversationMember.joined_at,
                ConversationMember.id,
            )
            .with_for_update()
        )
    )

    transferred_to_user_id = None

    if viewer.role == Role.OWNER and remaining:
        successor = remaining[0]
        successor.role = Role.OWNER

        transferred_to_user_id = str(
            successor.user_id
        )

    viewer.left_at = datetime.now(
        timezone.utc
    )

    if not remaining:
        group.is_active = False

    await session.commit()

    return {
        "ok": True,
        "transferred_to_user_id":
            transferred_to_user_id,
    }


@router.get("/{conversation_id}/messages/{message_id}/reactions")
async def message_reaction_people(
    conversation_id: uuid.UUID,
    message_id: uuid.UUID,
    session: AsyncSession = Depends(get_control_db),
    user: User = Depends(get_current_verified_user),
):
    await access(session, conversation_id, user.id)
    message = await session.scalar(select(ChatMessage).where(
        ChatMessage.id == message_id,
        ChatMessage.conversation_id == conversation_id,
        ChatMessage.deleted_at.is_(None),
    ))
    if message is None:
        raise HTTPException(404, "Message not found.")
    rows = (await session.execute(
        select(ChatMessageReaction, User)
        .join(User, User.id == ChatMessageReaction.user_id)
        .where(ChatMessageReaction.message_id == message_id)
        .order_by(ChatMessageReaction.emoji, User.id)
    )).all()
    return {
        "message_id": str(message_id),
        "counts": dict(Counter(reaction.emoji for reaction, _ in rows)),
        "items": [
            {
                "user_id": str(reaction.user_id),
                "emoji": reaction.emoji,
                "mine": reaction.user_id == user.id,
                "name": getattr(person, "name", None) or getattr(person, "full_name", None),
                "username": getattr(person, "username", None),
                "avatar_url": getattr(person, "avatar_url", None),
            }
            for reaction, person in rows
        ],
    }
@router.get("/{conversation_id}/hidden-messages")
async def list_hidden_messages(
    conversation_id: uuid.UUID,
    session: AsyncSession = Depends(get_control_db),
    user: User = Depends(get_current_verified_user),
):
    from sqlalchemy import text

    await access(
        session,
        conversation_id,
        user.id,
    )

    result = await session.execute(
        text("""
            SELECT message_id
            FROM chat_group_hidden_messages
            WHERE conversation_id = :conversation_id
              AND user_id = :user_id
        """),
        {
            "conversation_id": conversation_id,
            "user_id": user.id,
        },
    )

    return {
        "message_ids": [
            str(message_id)
            for message_id in result.scalars().all()
        ]
    }


@router.post(
    "/{conversation_id}/messages/{message_id}/hide"
)
async def hide_message_for_me(
    conversation_id: uuid.UUID,
    message_id: uuid.UUID,
    session: AsyncSession = Depends(get_control_db),
    user: User = Depends(get_current_verified_user),
):
    from sqlalchemy import text

    await access(
        session,
        conversation_id,
        user.id,
    )

    message = await session.scalar(
        select(ChatMessage).where(
            ChatMessage.id == message_id,
            ChatMessage.conversation_id == conversation_id,
            ChatMessage.deleted_at.is_(None),
        )
    )

    if message is None:
        raise HTTPException(
            status_code=404,
            detail="Message not found.",
        )

    await session.execute(
        text("""
            INSERT INTO chat_group_hidden_messages (
                conversation_id,
                message_id,
                user_id
            )
            VALUES (
                :conversation_id,
                :message_id,
                :user_id
            )
            ON CONFLICT (message_id, user_id)
            DO NOTHING
        """),
        {
            "conversation_id": conversation_id,
            "message_id": message_id,
            "user_id": user.id,
        },
    )

    await session.commit()

    return {
        "message_id": str(message_id),
        "hidden": True,
    }