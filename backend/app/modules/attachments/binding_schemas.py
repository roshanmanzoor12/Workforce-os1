from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.attachments.models import (
    AttachmentKind,
    AttachmentScope,
)


class AttachmentBindRequest(BaseModel):
    attachment_ids: list[uuid.UUID] = Field(
        min_length=1,
        max_length=10,
    )


class BoundAttachmentResponse(BaseModel):
    attachment_id: uuid.UUID
    message_id: uuid.UUID

    scope: AttachmentScope

    conversation_id: uuid.UUID | None = None
    channel_id: uuid.UUID | None = None

    kind: AttachmentKind

    filename: str
    content_type: str
    size_bytes: int

    ready_at: datetime | None = None


class AttachmentBindResponse(BaseModel):
    message_id: uuid.UUID

    attachments: list[
        BoundAttachmentResponse
    ]


class MessageAttachmentsResponse(BaseModel):
    message_id: uuid.UUID

    attachments: list[
        BoundAttachmentResponse
    ]