from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.modules.attachments.models import (
    AttachmentKind,
    AttachmentScope,
    AttachmentStatus,
)


class AttachmentPrepareRequest(BaseModel):
    scope: AttachmentScope

    conversation_id: uuid.UUID | None = None
    channel_id: uuid.UUID | None = None
    personal_note_id: uuid.UUID | None = None

    filename: str = Field(
        min_length=1,
        max_length=255,
    )

    content_type: str = Field(
        min_length=1,
        max_length=255,
    )

    size_bytes: int = Field(ge=1)

    @field_validator(
        "filename",
        "content_type",
        mode="before",
    )
    @classmethod
    def strip_metadata(cls, value):
        if isinstance(value, str):
            return value.strip()

        return value

    @model_validator(mode="after")
    def validate_target(self) -> AttachmentPrepareRequest:
        if (
            self.scope != AttachmentScope.NOTE
            and self.personal_note_id is not None
        ):
            raise ValueError(
                "personal_note_id is only valid for NOTE scope."
            )

        if self.scope == AttachmentScope.NOTE:
            if (
                self.personal_note_id is None
                or self.conversation_id is not None
                or self.channel_id is not None
            ):
                raise ValueError(
                    "NOTE scope requires personal_note_id "
                    "and no conversation_id or channel_id."
                )

        elif self.scope == AttachmentScope.CONVERSATION:
            if (
                self.conversation_id is None
                or self.channel_id is not None
            ):
                raise ValueError(
                    "CONVERSATION scope requires conversation_id "
                    "and no channel_id."
                )

        elif self.scope == AttachmentScope.CHANNEL:
            if (
                self.channel_id is None
                or self.conversation_id is not None
            ):
                raise ValueError(
                    "CHANNEL scope requires channel_id "
                    "and no conversation_id."
                )

        return self


class AttachmentPrepareResponse(BaseModel):
    attachment_id: uuid.UUID
    upload_url: str
    upload_method: str = "PUT"
    expires_in_seconds: int
    max_size_bytes: int


class AttachmentCompleteRequest(BaseModel):
    checksum_sha256: str | None = Field(
        default=None,
        min_length=64,
        max_length=64,
        pattern=r"^[a-fA-F0-9]{64}$",
    )


class AttachmentResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: uuid.UUID
    owner_user_id: uuid.UUID

    scope: AttachmentScope
    conversation_id: uuid.UUID | None
    channel_id: uuid.UUID | None
    message_id: uuid.UUID | None
    personal_note_id: uuid.UUID | None = None

    kind: AttachmentKind
    status: AttachmentStatus

    original_filename: str
    content_type: str
    size_bytes: int

    created_at: datetime
    ready_at: datetime | None


class AttachmentDownloadResponse(BaseModel):
    attachment_id: uuid.UUID
    download_url: str
    expires_in_seconds: int


class AttachmentPlanLimitResponse(BaseModel):
    plan: str
    max_size_bytes: int
    max_size_mb: int


class AttachmentListResponse(BaseModel):
    items: list[AttachmentResponse]