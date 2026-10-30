from __future__ import annotations

import uuid

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.core.database import (
    get_control_db,
)
from app.modules.attachments.binding_schemas import (
    AttachmentBindRequest,
    AttachmentBindResponse,
    MessageAttachmentsResponse,
)
from app.modules.attachments.binding_service import (
    AttachmentBindingService,
)
from app.modules.attachments.storage import (
    get_attachment_storage,
)
from app.modules.auth.permissions import (
    get_current_verified_user,
)
from app.modules.channels.models import (
    WorkspaceChannel,
)
from app.modules.channels.realtime_attachment_bridge import (
    channel_realtime_attachment_bridge,
)


# =========================================================
# ROUTER
# =========================================================


router = APIRouter(
    tags=[
        "attachment-message-bindings",
    ],
)


# =========================================================
# HELPERS
# =========================================================


def _user_id(
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
        str(
            value
        )
    )


def _service(
    session: AsyncSession,
) -> AttachmentBindingService:
    """
    Construct the attachment binding service using its real
    constructor contract.

    AttachmentBindingService owns creation of:

        AttachmentBindingRepository
        AttachmentService
        AttachmentRealtimePublisher

    The router therefore supplies only:

        session
        storage
    """

    return AttachmentBindingService(
        session=session,
        storage=get_attachment_storage(),
    )


async def _workspace_id_for_channel(
    *,
    session: AsyncSession,
    channel_id: uuid.UUID,
) -> uuid.UUID:
    """
    Resolve the workspace that owns an active channel.

    This value is server-resolved and is used only for publishing
    the canonical workspace-channel realtime attachment event.
    """

    result = await session.execute(
        select(
            WorkspaceChannel.workspace_id
        ).where(
            WorkspaceChannel.id
            == channel_id,
            WorkspaceChannel.is_active.is_(
                True
            ),
        )
    )

    workspace_id = (
        result.scalar_one_or_none()
    )

    if workspace_id is None:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=(
                "Workspace channel not found."
            ),
        )

    return workspace_id


# =========================================================
# CONVERSATION — BIND
# =========================================================


@router.post(
    (
        "/chat/{conversation_id}/"
        "messages/{message_id}/"
        "attachments"
    ),
    response_model=(
        AttachmentBindResponse
    ),
)
async def bind_conversation_attachments(
    conversation_id: uuid.UUID,
    message_id: uuid.UUID,
    payload: AttachmentBindRequest,
    session: AsyncSession = Depends(
        get_control_db
    ),
    current_user=Depends(
        get_current_verified_user
    ),
) -> AttachmentBindResponse:
    service = _service(
        session
    )

    attachments = (
        await service.bind_conversation(
            user_id=_user_id(
                current_user
            ),
            conversation_id=(
                conversation_id
            ),
            message_id=message_id,
            attachment_ids=(
                payload.attachment_ids
            ),
        )
    )

    return AttachmentBindResponse(
        message_id=message_id,
        attachments=[
            service.serialize(
                item
            )
            for item
            in attachments
        ],
    )


# =========================================================
# CONVERSATION — LIST
# =========================================================


@router.get(
    (
        "/chat/{conversation_id}/"
        "messages/{message_id}/"
        "attachments"
    ),
    response_model=(
        MessageAttachmentsResponse
    ),
)
async def list_conversation_attachments(
    conversation_id: uuid.UUID,
    message_id: uuid.UUID,
    session: AsyncSession = Depends(
        get_control_db
    ),
    current_user=Depends(
        get_current_verified_user
    ),
) -> MessageAttachmentsResponse:
    service = _service(
        session
    )

    attachments = (
        await service
        .list_conversation_message(
            user_id=_user_id(
                current_user
            ),
            conversation_id=(
                conversation_id
            ),
            message_id=message_id,
        )
    )

    return MessageAttachmentsResponse(
        message_id=message_id,
        attachments=[
            service.serialize(
                item
            )
            for item
            in attachments
        ],
    )


# =========================================================
# CHANNEL — BIND + REALTIME
# =========================================================


@router.post(
    (
        "/workspace-channels/"
        "{channel_id}/messages/"
        "{message_id}/attachments"
    ),
    response_model=(
        AttachmentBindResponse
    ),
)
async def bind_channel_attachments(
    channel_id: uuid.UUID,
    message_id: uuid.UUID,
    payload: AttachmentBindRequest,
    session: AsyncSession = Depends(
        get_control_db
    ),
    current_user=Depends(
        get_current_verified_user
    ),
) -> AttachmentBindResponse:
    service = _service(
        session
    )

    user_id = _user_id(
        current_user
    )

    # Resolve workspace identity before mutation/publish.
    #
    # The client never supplies workspace_id for this route.
    # It is derived from the trusted channel row.

    workspace_id = (
        await _workspace_id_for_channel(
            session=session,
            channel_id=channel_id,
        )
    )

    # -----------------------------------------------------
    # DURABLE BINDING MUTATION
    # -----------------------------------------------------

    attachments = (
        await service.bind_channel(
            user_id=user_id,
            channel_id=channel_id,
            message_id=message_id,
            attachment_ids=(
                payload.attachment_ids
            ),
        )
    )

    response = (
        AttachmentBindResponse(
            message_id=message_id,
            attachments=[
                service.serialize(
                    item
                )
                for item
                in attachments
            ],
        )
    )

    # -----------------------------------------------------
    # CANONICAL CHANNEL REALTIME EVENT
    # -----------------------------------------------------
    #
    # BindingService commits the durable attachment mutation.
    #
    # The channel bridge publishes the workspace-channel
    # canonical event:
    #
    #     channel.attachment.bound
    #
    # Publication remains best-effort inside the bridge so
    # realtime infrastructure cannot roll back a successful
    # durable attachment binding.

    await (
        channel_realtime_attachment_bridge
        .publish_bound(
            workspace_id=workspace_id,
            channel_id=channel_id,
            message_id=message_id,
            attachment_ids=[
                item.id
                for item
                in attachments
            ],
            actor_user_id=user_id,
        )
    )

    return response


# =========================================================
# CHANNEL — LIST
# =========================================================


@router.get(
    (
        "/workspace-channels/"
        "{channel_id}/messages/"
        "{message_id}/attachments"
    ),
    response_model=(
        MessageAttachmentsResponse
    ),
)
async def list_channel_attachments(
    channel_id: uuid.UUID,
    message_id: uuid.UUID,
    session: AsyncSession = Depends(
        get_control_db
    ),
    current_user=Depends(
        get_current_verified_user
    ),
) -> MessageAttachmentsResponse:
    service = _service(
        session
    )

    attachments = (
        await service
        .list_channel_message(
            user_id=_user_id(
                current_user
            ),
            channel_id=channel_id,
            message_id=message_id,
        )
    )

    return MessageAttachmentsResponse(
        message_id=message_id,
        attachments=[
            service.serialize(
                item
            )
            for item
            in attachments
        ],
    )


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "router",
]