from __future__ import annotations

import importlib
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.attachments.models import (
    Attachment,
    AttachmentScope,
    AttachmentStatus,
)


class AttachmentBindingRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    @staticmethod
    def _resolve_message_model(
        *,
        module_name: str,
        target_column: str,
    ):
        module = importlib.import_module(
            module_name
        )

        matches = []

        for value in vars(module).values():
            if not isinstance(value, type):
                continue

            table = getattr(
                value,
                "__table__",
                None,
            )

            if table is None:
                continue

            columns = {
                column.name
                for column
                in table.columns
            }

            required = {
                "id",
                target_column,
            }

            if not required.issubset(
                columns
            ):
                continue

            name = value.__name__.lower()

            if "message" not in name:
                continue

            matches.append(value)

        if len(matches) != 1:
            raise RuntimeError(
                "Unable to uniquely resolve "
                f"message model in {module_name} "
                f"for {target_column}. "
                f"Found {len(matches)} candidates."
            )

        return matches[0]

    async def conversation_message_exists(
        self,
        *,
        conversation_id: uuid.UUID,
        message_id: uuid.UUID,
    ) -> bool:
        model = self._resolve_message_model(
            module_name=(
                "app.modules.chat.models"
            ),
            target_column="conversation_id",
        )

        statement = (
            select(model.id)
            .where(
                model.id == message_id,
                model.conversation_id
                == conversation_id,
            )
            .limit(1)
        )

        result = await self.session.execute(
            statement
        )

        return (
            result.scalar_one_or_none()
            is not None
        )

    async def channel_message_exists(
        self,
        *,
        channel_id: uuid.UUID,
        message_id: uuid.UUID,
    ) -> bool:
        model = self._resolve_message_model(
            module_name=(
                "app.modules.channels.models"
            ),
            target_column="channel_id",
        )

        statement = (
            select(model.id)
            .where(
                model.id == message_id,
                model.channel_id
                == channel_id,
            )
            .limit(1)
        )

        result = await self.session.execute(
            statement
        )

        return (
            result.scalar_one_or_none()
            is not None
        )

    async def get_attachment(
        self,
        *,
        attachment_id: uuid.UUID,
    ) -> Attachment | None:
        result = await self.session.execute(
            select(Attachment).where(
                Attachment.id
                == attachment_id
            )
        )

        return result.scalar_one_or_none()

    async def list_message_attachments(
        self,
        *,
        message_id: uuid.UUID,
        scope: AttachmentScope,
        conversation_id: uuid.UUID | None = None,
        channel_id: uuid.UUID | None = None,
    ) -> list[Attachment]:
        statement = (
            select(Attachment)
            .where(
                Attachment.message_id
                == message_id,
                Attachment.scope
                == scope,
                Attachment.status
                == AttachmentStatus.READY,
            )
            .order_by(
                Attachment.created_at.asc()
            )
        )

        if (
            scope
            == AttachmentScope.CONVERSATION
        ):
            statement = statement.where(
                Attachment.conversation_id
                == conversation_id
            )

        if (
            scope
            == AttachmentScope.CHANNEL
        ):
            statement = statement.where(
                Attachment.channel_id
                == channel_id
            )

        result = await self.session.execute(
            statement
        )

        return list(
            result.scalars().all()
        )

    async def list_orphan_pending(
        self,
        *,
        older_than: datetime,
        limit: int = 100,
    ) -> list[Attachment]:
        statement = (
            select(Attachment)
            .where(
                Attachment.status
                == AttachmentStatus.PENDING,
                Attachment.message_id.is_(None),
                Attachment.created_at
                < older_than,
            )
            .order_by(
                Attachment.created_at.asc()
            )
            .limit(limit)
        )

        result = await self.session.execute(
            statement
        )

        return list(
            result.scalars().all()
        )