from __future__ import annotations

import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import PurePath

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.attachments.limits import (
    get_attachment_limit_bytes,
    validate_attachment_size,
)
from app.modules.attachments.models import (
    Attachment,
    AttachmentKind,
    AttachmentScope,
    AttachmentStatus,
)
from app.modules.attachments.schemas import (
    AttachmentPrepareRequest,
)
from app.modules.attachments.storage import (
    AttachmentStorage,
)


SAFE_FILENAME_PATTERN = re.compile(
    r"[^A-Za-z0-9._-]+"
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def classify_attachment_kind(
    content_type: str,
) -> AttachmentKind:
    normalized = content_type.lower().strip()

    if normalized.startswith("image/"):
        return AttachmentKind.IMAGE

    if normalized.startswith("video/"):
        return AttachmentKind.VIDEO

    if normalized.startswith("audio/"):
        return AttachmentKind.AUDIO

    return AttachmentKind.FILE


def sanitize_filename(
    filename: str,
) -> str:
    name = PurePath(filename).name.strip()

    if not name:
        name = "file"

    safe = SAFE_FILENAME_PATTERN.sub(
        "_",
        name,
    )

    safe = safe[:200]

    if not safe:
        return "file"

    return safe


class AttachmentService:
    def __init__(
        self,
        *,
        db: AsyncSession,
        storage: AttachmentStorage,
    ) -> None:
        self.db = db
        self.storage = storage

    async def _conversation_access_allowed(
        self,
        *, 
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
    ) -> bool:
        from app.modules.chat.models import ConversationMember

        result = await self.db.execute(
            select(
                ConversationMember.id
            ).where(
                ConversationMember.conversation_id
                == conversation_id,
                ConversationMember.user_id
                == user_id,
                ConversationMember.left_at.is_(
                    None
                ),
            )
        )

        return (
            result.scalar_one_or_none()
            is not None
        )

    async def _channel_access_allowed(
        self,
        *,
        user_id: uuid.UUID,
        channel_id: uuid.UUID,
    ) -> bool:
        from app.modules.channels.models import (
            WorkspaceChannel,
            WorkspaceChannelMember,
        )

        result = await self.db.execute(
            select(
                WorkspaceChannelMember.id
            )
            .join(
                WorkspaceChannel,
                WorkspaceChannel.id
                == WorkspaceChannelMember.channel_id,
            )
            .where(
                WorkspaceChannelMember.channel_id
                == channel_id,
                WorkspaceChannelMember.user_id
                == user_id,
                WorkspaceChannelMember.left_at.is_(
                    None
                ),
                WorkspaceChannel.is_active.is_(
                    True
                ),
            )
        )

        return (
            result.scalar_one_or_none()
            is not None
        )

    async def assert_scope_access(
        self,
        *,
        user_id: uuid.UUID,
        scope: AttachmentScope,
        conversation_id: uuid.UUID | None,
        channel_id: uuid.UUID | None,
    ) -> None:
        if (
            scope
            == AttachmentScope.CONVERSATION
        ):
            if conversation_id is None:
                raise HTTPException(
                    status_code=(
                        status.HTTP_422_UNPROCESSABLE_ENTITY
                    ),
                    detail=(
                        "conversation_id is required "
                        "for conversation attachments."
                    ),
                )

            if channel_id is not None:
                raise HTTPException(
                    status_code=(
                        status.HTTP_422_UNPROCESSABLE_ENTITY
                    ),
                    detail=(
                        "channel_id must be empty "
                        "for conversation attachments."
                    ),
                )

            allowed = (
                await self
                ._conversation_access_allowed(
                    user_id=user_id,
                    conversation_id=(
                        conversation_id
                    ),
                )
            )

            if not allowed:
                raise HTTPException(
                    status_code=(
                        status.HTTP_403_FORBIDDEN
                    ),
                    detail=(
                        "Conversation attachment "
                        "access denied."
                    ),
                )

            return

        if scope == AttachmentScope.CHANNEL:
            if channel_id is None:
                raise HTTPException(
                    status_code=(
                        status.HTTP_422_UNPROCESSABLE_ENTITY
                    ),
                    detail=(
                        "channel_id is required "
                        "for channel attachments."
                    ),
                )

            if conversation_id is not None:
                raise HTTPException(
                    status_code=(
                        status.HTTP_422_UNPROCESSABLE_ENTITY
                    ),
                    detail=(
                        "conversation_id must be empty "
                        "for channel attachments."
                    ),
                )

            allowed = (
                await self
                ._channel_access_allowed(
                    user_id=user_id,
                    channel_id=channel_id,
                )
            )

            if not allowed:
                raise HTTPException(
                    status_code=(
                        status.HTTP_403_FORBIDDEN
                    ),
                    detail=(
                        "Channel attachment "
                        "access denied."
                    ),
                )

            return

        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=(
                "Unsupported attachment scope."
            ),
        )

    async def prepare(
        self,
        *,
        user_id: uuid.UUID,
        plan_code: str,
        request: AttachmentPrepareRequest,
    ) -> tuple[
        Attachment,
        str,
        int,
    ]:
        await self.assert_scope_access(
            user_id=user_id,
            scope=request.scope,
            conversation_id=(
                request.conversation_id
            ),
            channel_id=request.channel_id,
        )

        try:
            max_size = (
                validate_attachment_size(
                    plan_code=plan_code,
                    size_bytes=(
                        request.size_bytes
                    ),
                )
            )

        except ValueError as exc:
            raise HTTPException(
                status_code=(
                    status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
                ),
                detail=str(exc),
            ) from exc

        attachment_id = uuid.uuid4()

        safe_filename = sanitize_filename(
            request.filename
        )

        scope_segment = (
            request.scope.value.lower()
        )

        object_key = (
            f"{scope_segment}/"
            f"{user_id}/"
            f"{attachment_id}/"
            f"{safe_filename}"
        )

        attachment = Attachment(
            id=attachment_id,
            owner_user_id=user_id,
            scope=request.scope,
            conversation_id=(
                request.conversation_id
            ),
            channel_id=request.channel_id,
            kind=classify_attachment_kind(
                request.content_type
            ),
            status=AttachmentStatus.PENDING,
            original_filename=(
                request.filename
            ),
            content_type=(
                request.content_type
            ),
            size_bytes=request.size_bytes,
            bucket_name=(
                self.storage.bucket
            ),
            object_key=object_key,
        )

        self.db.add(
            attachment
        )

        await self.db.commit()
        await self.db.refresh(
            attachment
        )

        upload_expiry = int(
            os.getenv(
                "WORKFORCE_ATTACHMENT_UPLOAD_URL_SECONDS",
                "900",
            )
        )

        try:
            upload_url = (
                self.storage
                .create_upload_url(
                    object_key=object_key,
                    expires_seconds=(
                        upload_expiry
                    ),
                )
            )

        except Exception:
            attachment.status = (
                AttachmentStatus.FAILED
            )

            attachment.failure_reason = (
                "Unable to create object "
                "storage upload URL."
            )

            await self.db.commit()

            raise

        return (
            attachment,
            upload_url,
            max_size,
        )

    async def get_attachment(
        self,
        *,
        attachment_id: uuid.UUID,
    ) -> Attachment:
        result = await self.db.execute(
            select(
                Attachment
            ).where(
                Attachment.id
                == attachment_id
            )
        )

        attachment = (
            result.scalar_one_or_none()
        )

        if attachment is None:
            raise HTTPException(
                status_code=(
                    status.HTTP_404_NOT_FOUND
                ),
                detail=(
                    "Attachment not found."
                ),
            )

        return attachment

    async def assert_attachment_access(
        self,
        *,
        attachment: Attachment,
        user_id: uuid.UUID,
    ) -> None:
        await self.assert_scope_access(
            user_id=user_id,
            scope=attachment.scope,
            conversation_id=(
                attachment.conversation_id
            ),
            channel_id=(
                attachment.channel_id
            ),
        )

    async def complete(
        self,
        *,
        attachment_id: uuid.UUID,
        user_id: uuid.UUID,
        checksum_sha256: str | None,
    ) -> Attachment:
        attachment = (
            await self.get_attachment(
                attachment_id=(
                    attachment_id
                )
            )
        )

        await self.assert_attachment_access(
            attachment=attachment,
            user_id=user_id,
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
                    "Only the attachment "
                    "owner can complete "
                    "an upload."
                ),
            )

        if (
            attachment.status
            == AttachmentStatus.READY
        ):
            return attachment

        if (
            attachment.status
            != AttachmentStatus.PENDING
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Attachment is not "
                    "awaiting upload."
                ),
            )

        if not (
            self.storage.object_exists(
                object_key=(
                    attachment.object_key
                )
            )
        ):
            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Attachment object has "
                    "not been uploaded."
                ),
            )

        actual_size = (
            self.storage.object_size(
                object_key=(
                    attachment.object_key
                )
            )
        )

        if (
            actual_size
            != attachment.size_bytes
        ):
            self.storage.delete_object(
                object_key=(
                    attachment.object_key
                )
            )

            attachment.status = (
                AttachmentStatus.FAILED
            )

            attachment.failure_reason = (
                "Uploaded object size "
                "did not match declared "
                "attachment size."
            )

            await self.db.commit()

            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Uploaded attachment "
                    "size does not match "
                    "declared size."
                ),
            )

        attachment.status = (
            AttachmentStatus.READY
        )

        attachment.ready_at = (
            utcnow()
        )

        attachment.checksum_sha256 = (
            checksum_sha256.lower()
            if checksum_sha256
            else None
        )

        attachment.failure_reason = None

        await self.db.commit()

        await self.db.refresh(
            attachment
        )

        return attachment

    async def create_download_url(
        self,
        *,
        attachment_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> tuple[
        Attachment,
        str,
        int,
    ]:
        attachment = (
            await self.get_attachment(
                attachment_id=(
                    attachment_id
                )
            )
        )

        await self.assert_attachment_access(
            attachment=attachment,
            user_id=user_id,
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
                    "Attachment is not "
                    "ready for download."
                ),
            )

        expiry = int(
            os.getenv(
                "WORKFORCE_ATTACHMENT_DOWNLOAD_URL_SECONDS",
                "300",
            )
        )

        download_url = (
            self.storage.create_download_url(
                object_key=attachment.object_key,
                expires_seconds=expiry,
                download_filename=(
                    attachment.original_filename
                ),
                content_type=(
                    attachment.content_type
                ),
            )
        )

        return (
            attachment,
            download_url,
            expiry,
        )

    async def delete(
        self,
        *,
        attachment_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        attachment = (
            await self.get_attachment(
                attachment_id=(
                    attachment_id
                )
            )
        )

        await self.assert_attachment_access(
            attachment=attachment,
            user_id=user_id,
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
                    "Only the attachment "
                    "owner can delete "
                    "this attachment."
                ),
            )

        if (
            attachment.status
            == AttachmentStatus.DELETED
        ):
            return

        if self.storage.object_exists(
            object_key=(
                attachment.object_key
            )
        ):
            self.storage.delete_object(
                object_key=(
                    attachment.object_key
                )
            )

        attachment.status = (
            AttachmentStatus.DELETED
        )

        attachment.deleted_at = (
            utcnow()
        )

        await self.db.commit()

    async def bind_to_message(
        self,
        *,
        attachment_id: uuid.UUID,
        user_id: uuid.UUID,
        message_id: uuid.UUID,
    ) -> Attachment:
        attachment = (
            await self.get_attachment(
                attachment_id=(
                    attachment_id
                )
            )
        )

        await self.assert_attachment_access(
            attachment=attachment,
            user_id=user_id,
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
                    "Only the attachment "
                    "owner can bind it "
                    "to a message."
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
                    "Attachment must be "
                    "READY before message "
                    "binding."
                ),
            )

        if (
            attachment.message_id
            is not None
        ):
            if (
                attachment.message_id
                == message_id
            ):
                return attachment

            raise HTTPException(
                status_code=(
                    status.HTTP_409_CONFLICT
                ),
                detail=(
                    "Attachment is already "
                    "bound to another "
                    "message."
                ),
            )

        attachment.message_id = (
            message_id
        )

        await self.db.commit()

        await self.db.refresh(
            attachment
        )

        return attachment


__all__ = [
    "AttachmentService",
    "classify_attachment_kind",
    "sanitize_filename",
    "utcnow",
]