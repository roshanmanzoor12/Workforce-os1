from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from .enums import (
    WorkspaceChannelRole,
    WorkspaceChannelType,
)
from .models import (
    WorkspaceChannel,
    WorkspaceChannelMember,
    WorkspaceChannelMessage,
)
from .repository import WorkspaceChannelRepository
from .schemas import make_channel_slug


class WorkspaceChannelError(ValueError):
    pass


class WorkspaceChannelNotFoundError(
    WorkspaceChannelError
):
    pass


class WorkspaceChannelPermissionError(
    WorkspaceChannelError
):
    pass


class WorkspaceChannelConflictError(
    WorkspaceChannelError
):
    pass


class WorkspaceChannelService:
    CHANNELS_CREATE = "channels.create"
    CHANNELS_READ = "channels.read"
    CHANNELS_MANAGE = "channels.manage"

    def __init__(
        self,
        session: AsyncSession,
        *,
        repository: WorkspaceChannelRepository | None = None,
    ) -> None:
        self.session = session
        self.repository = (
            repository or WorkspaceChannelRepository()
        )

    async def create_channel(
        self,
        *,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
        name: str,
        channel_type: WorkspaceChannelType,
    ) -> WorkspaceChannel:
        required_permission = self.CHANNELS_CREATE

        owned = await self.repository.workspace_owned_by_user(
            self.session,
            workspace_id=workspace_id,
            user_id=user_id,
        )

        if not owned:
            raise WorkspaceChannelPermissionError(
                f"Permission required: {required_permission}"
            )

        normalized_name = name.strip()

        if not normalized_name:
            raise WorkspaceChannelError(
                "Channel name cannot be empty."
            )

        slug = make_channel_slug(normalized_name)

        existing = await self.repository.get_by_slug(
            self.session,
            workspace_id=workspace_id,
            slug=slug,
        )

        if existing is not None:
            raise WorkspaceChannelConflictError(
                "A channel with this name already exists."
            )

        channel = await self.repository.create_channel(
            self.session,
            workspace_id=workspace_id,
            user_id=user_id,
            name=normalized_name,
            slug=slug,
            channel_type=channel_type,
        )

        await self.repository.add_owner(
            self.session,
            channel_id=channel.id,
            user_id=user_id,
        )

        return channel

    async def list_channels(
        self,
        *,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> list[WorkspaceChannel]:
        required_permission = self.CHANNELS_READ

        channels = await self.repository.list_for_user(
            self.session,
            workspace_id=workspace_id,
            user_id=user_id,
        )

        if channels is None:
            raise WorkspaceChannelPermissionError(
                f"Permission required: {required_permission}"
            )

        return channels

    async def rename_channel(
        self,
        *,
        channel_id: uuid.UUID,
        user_id: uuid.UUID,
        name: str,
    ) -> WorkspaceChannel:
        channel = await self._require_channel(channel_id)

        await self._require_manager(
            channel_id=channel.id,
            user_id=user_id,
        )

        normalized_name = name.strip()

        if not normalized_name:
            raise WorkspaceChannelError(
                "Channel name cannot be empty."
            )

        new_slug = make_channel_slug(normalized_name)

        existing = await self.repository.get_by_slug(
            self.session,
            workspace_id=channel.workspace_id,
            slug=new_slug,
        )

        if existing is not None and existing.id != channel.id:
            raise WorkspaceChannelConflictError(
                "A channel with this name already exists."
            )

        channel.name = normalized_name
        channel.slug = new_slug

        await self.session.flush()

        return channel

    async def archive_channel(
        self,
        *,
        channel_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> WorkspaceChannel:
        channel = await self._require_channel(channel_id)

        await self._require_manager(
            channel_id=channel.id,
            user_id=user_id,
        )

        channel.is_active = False

        await self.session.flush()

        return channel

    async def send_message(
        self,
        *,
        channel_id: uuid.UUID,
        user_id: uuid.UUID,
        content: str,
    ) -> WorkspaceChannelMessage:
        channel = await self._require_channel(channel_id)

        await self._require_active_member(
            channel_id=channel.id,
            user_id=user_id,
        )

        normalized_content = content.strip()

        if not normalized_content:
            raise WorkspaceChannelError(
                "Message content cannot be empty."
            )

        return await self.repository.create_message(
            self.session,
            channel_id=channel.id,
            sender_user_id=user_id,
            content=normalized_content,
        )

    async def list_messages(
        self,
        *,
        channel_id: uuid.UUID,
        user_id: uuid.UUID,
        limit: int = 50,
    ) -> list[WorkspaceChannelMessage]:
        channel = await self._require_channel(channel_id)

        await self._require_active_member(
            channel_id=channel.id,
            user_id=user_id,
        )

        return await self.repository.list_messages(
            self.session,
            channel_id=channel.id,
            limit=limit,
        )

    async def update_message(
        self,
        *,
        channel_id: uuid.UUID,
        message_id: uuid.UUID,
        user_id: uuid.UUID,
        content: str,
    ) -> WorkspaceChannelMessage:
        channel = await self._require_channel(channel_id)

        member = await self._require_active_member(
            channel_id=channel.id,
            user_id=user_id,
        )

        message = await self.repository.get_message(
            self.session,
            channel_id=channel.id,
            message_id=message_id,
        )

        if message is None:
            raise WorkspaceChannelNotFoundError(
                "Workspace channel message not found."
            )

        is_manager = member.role in {
            WorkspaceChannelRole.OWNER,
            WorkspaceChannelRole.ADMIN,
        }

        if (
            message.sender_user_id != user_id
            and not is_manager
        ):
            raise WorkspaceChannelPermissionError(
                "Only the message author or a channel "
                "manager can edit this message."
            )

        normalized_content = content.strip()

        if not normalized_content:
            raise WorkspaceChannelError(
                "Message content cannot be empty."
            )

        return await self.repository.update_message(
            self.session,
            message=message,
            content=normalized_content,
            edited_at=datetime.now(timezone.utc),
        )

    async def delete_message(
        self,
        *,
        channel_id: uuid.UUID,
        message_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> WorkspaceChannelMessage:
        channel = await self._require_channel(channel_id)

        member = await self._require_active_member(
            channel_id=channel.id,
            user_id=user_id,
        )

        message = await self.repository.get_message(
            self.session,
            channel_id=channel.id,
            message_id=message_id,
        )

        if message is None:
            raise WorkspaceChannelNotFoundError(
                "Workspace channel message not found."
            )

        is_manager = member.role in {
            WorkspaceChannelRole.OWNER,
            WorkspaceChannelRole.ADMIN,
        }

        if (
            message.sender_user_id != user_id
            and not is_manager
        ):
            raise WorkspaceChannelPermissionError(
                "Only the message author or a channel "
                "manager can delete this message."
            )

        return await self.repository.delete_message(
            self.session,
            message=message,
            deleted_at=datetime.now(timezone.utc),
        )

    async def _require_channel(
        self,
        channel_id: uuid.UUID,
    ) -> WorkspaceChannel:
        channel = await self.repository.get_channel(
            self.session,
            channel_id=channel_id,
        )

        if channel is None or not channel.is_active:
            raise WorkspaceChannelNotFoundError(
                "Workspace channel not found."
            )

        return channel

    async def _require_active_member(
        self,
        *,
        channel_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> WorkspaceChannelMember:
        member = await self.repository.get_member(
            self.session,
            channel_id=channel_id,
            user_id=user_id,
        )

        if member is None or member.left_at is not None:
            raise WorkspaceChannelPermissionError(
                "User is not an active channel member."
            )

        return member

    async def _require_manager(
        self,
        *,
        channel_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> WorkspaceChannelMember:
        required_permission = self.CHANNELS_MANAGE

        member = await self._require_active_member(
            channel_id=channel_id,
            user_id=user_id,
        )

        if member.role not in {
            WorkspaceChannelRole.OWNER,
            WorkspaceChannelRole.ADMIN,
        }:
            raise WorkspaceChannelPermissionError(
                f"Permission required: {required_permission}"
            )

        return member


__all__ = [
    "WorkspaceChannelConflictError",
    "WorkspaceChannelError",
    "WorkspaceChannelNotFoundError",
    "WorkspaceChannelPermissionError",
    "WorkspaceChannelService",
]