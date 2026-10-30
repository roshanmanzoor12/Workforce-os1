from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.attachments.binding_repository import (
    AttachmentBindingRepository,
)
from app.modules.attachments.binding_schemas import (
    BoundAttachmentResponse,
)
from app.modules.attachments.models import (
    Attachment,
    AttachmentScope,
    AttachmentStatus,
)
from app.modules.attachments.realtime_publisher import (
    AttachmentRealtimePublisher,
)
from app.modules.attachments.service import (
    AttachmentService,
)
from app.modules.attachments.storage import (
    AttachmentStorage,
)


class AttachmentBindingService:
    MAX_ATTACHMENTS_PER_MESSAGE = 10

    def __init__(
        self,
        *,
        session: AsyncSession,
        storage: AttachmentStorage,
    ) -> None:
        self.session = session

        self.repository = (
            AttachmentBindingRepository(
                session
            )
        )

        self.attachment_service = (
            AttachmentService(
                db=session,
                storage=storage,
            )
        )

        self.realtime = (
            AttachmentRealtimePublisher(
                session
            )
        )

    @staticmethod
    def serialize(
        attachment: Attachment,
    ) -> BoundAttachmentResponse:
        return BoundAttachmentResponse(
            attachment_id=attachment.id,
            message_id=attachment.message_id,
            scope=attachment.scope,
            conversation_id=(
                attachment.conversation_id
            ),
            channel_id=(
                attachment.channel_id
            ),
            kind=attachment.kind,
            filename=(
                attachment.original_filename
            ),
            content_type=(
                attachment.content_type
            ),
            size_bytes=attachment.size_bytes,
            ready_at=attachment.ready_at,
        )

    async def _validate_attachment(
        self,
        *,
        attachment_id: uuid.UUID,
        user_id: uuid.UUID,
        scope: AttachmentScope,
        conversation_id: uuid.UUID | None,
        channel_id: uuid.UUID | None,
    ) -> Attachment:
        attachment = (
            await self.repository.get_attachment(
                attachment_id=attachment_id
            )
        )

        if attachment is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail="Attachment not found.",
            )

        if (
            attachment.owner_user_id
            != user_id
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_403_FORBIDDEN
                ),
                detail=(
                    "Only the uploader can bind "
                    "this attachment."
                ),
            )

        if (
            attachment.status
            != AttachmentStatus.READY
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Attachment must be READY "
                    "before message binding."
                ),
            )

        if attachment.scope != scope:
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Attachment scope does not "
                    "match message scope."
                ),
            )

        if (
            scope
            == AttachmentScope.CONVERSATION
        ):
            if (
                attachment.conversation_id
                != conversation_id
            ):
                raise HTTPException(
                    status_code=(
                        status.HTTP_409_CONFLICT
                    ),
                    detail=(
                        "Attachment belongs to "
                        "another conversation."
                    ),
                )

        if (
            scope
            == AttachmentScope.CHANNEL
        ):
            if (
                attachment.channel_id
                != channel_id
            ):
                raise HTTPException(
                    status_code=(
                        status.HTTP_409_CONFLICT
                    ),
                    detail=(
                        "Attachment belongs to "
                        "another channel."
                    ),
                )

        return attachment

    async def bind_conversation(
        self,
        *,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        message_id: uuid.UUID,
        attachment_ids: list[uuid.UUID],
    ) -> list[Attachment]:
        if (
            len(attachment_ids)
            > self.MAX_ATTACHMENTS_PER_MESSAGE
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_422_UNPROCESSABLE_ENTITY
                ),
                detail=(
                    "Maximum 10 attachments "
                    "per message."
                ),
            )

        await (
            self.attachment_service
            .assert_scope_access(
                user_id=user_id,
                scope=(
                    AttachmentScope.CONVERSATION
                ),
                conversation_id=conversation_id,
                channel_id=None,
            )
        )

        exists = (
            await self.repository
            .conversation_message_exists(
                conversation_id=(
                    conversation_id
                ),
                message_id=message_id,
            )
        )

        if not exists:
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Conversation message "
                    "not found."
                ),
            )

        attachments: list[
            Attachment
        ] = []

        for attachment_id in attachment_ids:
            attachment = (
                await self._validate_attachment(
                    attachment_id=attachment_id,
                    user_id=user_id,
                    scope=(
                        AttachmentScope.CONVERSATION
                    ),
                    conversation_id=(
                        conversation_id
                    ),
                    channel_id=None,
                )
            )

            if (
                attachment.message_id
                is not None
                and attachment.message_id
                != message_id
            ):
                raise HTTPException(
                    status_code=(
                        status.HTTP_409_CONFLICT
                    ),
                    detail=(
                        "Attachment is already "
                        "bound to another message."
                    ),
                )

            attachment.message_id = (
                message_id
            )

            attachments.append(
                attachment
            )

        await self.session.commit()

        await self.realtime.attachments_bound(
            actor_user_id=user_id,
            message_id=message_id,
            attachments=attachments,
        )

        return attachments

    async def bind_channel(
        self,
        *,
        user_id: uuid.UUID,
        channel_id: uuid.UUID,
        message_id: uuid.UUID,
        attachment_ids: list[uuid.UUID],
    ) -> list[Attachment]:
        if (
            len(attachment_ids)
            > self.MAX_ATTACHMENTS_PER_MESSAGE
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_422_UNPROCESSABLE_ENTITY
                ),
                detail=(
                    "Maximum 10 attachments "
                    "per message."
                ),
            )

        await (
            self.attachment_service
            .assert_scope_access(
                user_id=user_id,
                scope=AttachmentScope.CHANNEL,
                conversation_id=None,
                channel_id=channel_id,
            )
        )

        exists = (
            await self.repository
            .channel_message_exists(
                channel_id=channel_id,
                message_id=message_id,
            )
        )

        if not exists:
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Channel message not found."
                ),
            )

        attachments: list[
            Attachment
        ] = []

        for attachment_id in attachment_ids:
            attachment = (
                await self._validate_attachment(
                    attachment_id=attachment_id,
                    user_id=user_id,
                    scope=(
                        AttachmentScope.CHANNEL
                    ),
                    conversation_id=None,
                    channel_id=channel_id,
                )
            )

            if (
                attachment.message_id
                is not None
                and attachment.message_id
                != message_id
            ):
                raise HTTPException(
                    status_code=(
                        status.HTTP_409_CONFLICT
                    ),
                    detail=(
                        "Attachment is already "
                        "bound to another message."
                    ),
                )

            attachment.message_id = (
                message_id
            )

            attachments.append(
                attachment
            )

        await self.session.commit()

        await self.realtime.attachments_bound(
            actor_user_id=user_id,
            message_id=message_id,
            attachments=attachments,
        )

        return attachments

    async def list_conversation_message(
        self,
        *,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        message_id: uuid.UUID,
    ) -> list[Attachment]:
        await (
            self.attachment_service
            .assert_scope_access(
                user_id=user_id,
                scope=(
                    AttachmentScope.CONVERSATION
                ),
                conversation_id=conversation_id,
                channel_id=None,
            )
        )

        return (
            await self.repository
            .list_message_attachments(
                message_id=message_id,
                scope=(
                    AttachmentScope.CONVERSATION
                ),
                conversation_id=conversation_id,
            )
        )

    async def list_channel_message(
        self,
        *,
        user_id: uuid.UUID,
        channel_id: uuid.UUID,
        message_id: uuid.UUID,
    ) -> list[Attachment]:
        await (
            self.attachment_service
            .assert_scope_access(
                user_id=user_id,
                scope=(
                    AttachmentScope.CHANNEL
                ),
                conversation_id=None,
                channel_id=channel_id,
            )
        )

        return (
            await self.repository
            .list_message_attachments(
                message_id=message_id,
                scope=(
                    AttachmentScope.CHANNEL
                ),
                channel_id=channel_id,
            )
        )