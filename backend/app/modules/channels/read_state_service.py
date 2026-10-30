from __future__ import annotations

import uuid
from datetime import (
    datetime,
    timezone,
)

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from .read_state_repository import (
    WorkspaceChannelReadStateRepository,
)
from .read_state_schemas import (
    WorkspaceChannelReadStatePublic,
    WorkspaceChannelUnreadListResponse,
    WorkspaceChannelUnreadSummary,
)


class WorkspaceChannelReadStateError(
    ValueError
):
    pass


class WorkspaceChannelReadStateNotFoundError(
    WorkspaceChannelReadStateError
):
    pass


class WorkspaceChannelReadStatePermissionError(
    WorkspaceChannelReadStateError
):
    pass


class WorkspaceChannelReadStateService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        repository: (
            WorkspaceChannelReadStateRepository
            | None
        ) = None,
    ) -> None:
        self.session = (
            session
        )

        self.repository = (
            repository
            or WorkspaceChannelReadStateRepository()
        )

    @staticmethod
    def _utcnow() -> datetime:
        return datetime.now(
            timezone.utc
        )

    async def _require_access(
        self,
        *,
        channel_id: uuid.UUID,
        user_id: uuid.UUID,
    ):
        channel = (
            await self.repository
            .get_channel(
                self.session,
                channel_id=channel_id,
            )
        )

        if (
            channel is None
            or not channel.is_active
        ):
            raise (
                WorkspaceChannelReadStateNotFoundError(
                    "Workspace channel not found."
                )
            )

        member = (
            await self.repository
            .get_active_member(
                self.session,
                channel_id=channel_id,
                user_id=user_id,
            )
        )

        if member is None:
            raise (
                WorkspaceChannelReadStatePermissionError(
                    "User is not an active "
                    "channel member."
                )
            )

        return channel

    async def get_summary(
        self,
        *,
        channel_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> WorkspaceChannelUnreadSummary:
        await self._require_access(
            channel_id=channel_id,
            user_id=user_id,
        )

        state = (
            await self.repository
            .get_state(
                self.session,
                channel_id=channel_id,
                user_id=user_id,
            )
        )

        last_read_at = (
            state.last_read_at
            if state is not None
            else None
        )

        unread = (
            await self.repository
            .unread_count(
                self.session,
                channel_id=channel_id,
                user_id=user_id,
                last_read_at=last_read_at,
            )
        )

        return (
            WorkspaceChannelUnreadSummary(
                channel_id=channel_id,
                unread_count=unread,
                last_read_message_id=(
                    state.last_read_message_id
                    if state is not None
                    else None
                ),
                last_read_at=(
                    last_read_at
                ),
            )
        )

    async def mark_message_read(
        self,
        *,
        channel_id: uuid.UUID,
        message_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> WorkspaceChannelReadStatePublic:
        await self._require_access(
            channel_id=channel_id,
            user_id=user_id,
        )

        message = (
            await self.repository
            .get_message(
                self.session,
                channel_id=channel_id,
                message_id=message_id,
            )
        )

        if (
            message is None
            or message.deleted_at
            is not None
        ):
            raise (
                WorkspaceChannelReadStateNotFoundError(
                    "Workspace channel message "
                    "not found."
                )
            )

        current = (
            await self.repository
            .get_state(
                self.session,
                channel_id=channel_id,
                user_id=user_id,
            )
        )

        target_read_at = (
            message.created_at
        )

        if (
            current is not None
            and current.last_read_at
            is not None
            and current.last_read_at
            >= target_read_at
        ):
            state = current

        else:
            state = (
                await self.repository
                .save_state(
                    self.session,
                    channel_id=channel_id,
                    user_id=user_id,
                    last_read_message_id=(
                        message.id
                    ),
                    last_read_at=(
                        target_read_at
                    ),
                )
            )

        unread = (
            await self.repository
            .unread_count(
                self.session,
                channel_id=channel_id,
                user_id=user_id,
                last_read_at=(
                    state.last_read_at
                ),
            )
        )

        return (
            WorkspaceChannelReadStatePublic(
                channel_id=channel_id,
                user_id=user_id,
                last_read_message_id=(
                    state.last_read_message_id
                ),
                last_read_at=(
                    state.last_read_at
                ),
                unread_count=unread,
            )
        )

    async def mark_all_read(
        self,
        *,
        channel_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> WorkspaceChannelReadStatePublic:
        await self._require_access(
            channel_id=channel_id,
            user_id=user_id,
        )

        latest = (
            await self.repository
            .latest_message(
                self.session,
                channel_id=channel_id,
            )
        )

        read_at = (
            latest.created_at
            if latest is not None
            else self._utcnow()
        )

        state = (
            await self.repository
            .save_state(
                self.session,
                channel_id=channel_id,
                user_id=user_id,
                last_read_message_id=(
                    latest.id
                    if latest is not None
                    else None
                ),
                last_read_at=read_at,
            )
        )

        return (
            WorkspaceChannelReadStatePublic(
                channel_id=channel_id,
                user_id=user_id,
                last_read_message_id=(
                    state.last_read_message_id
                ),
                last_read_at=(
                    state.last_read_at
                ),
                unread_count=0,
            )
        )

    async def list_workspace(
        self,
        *,
        workspace_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> WorkspaceChannelUnreadListResponse:
        channels = (
            await self.repository
            .list_active_channels(
                self.session,
                workspace_id=workspace_id,
                user_id=user_id,
            )
        )

        summaries: list[
            WorkspaceChannelUnreadSummary
        ] = []

        total_unread = 0

        for channel in channels:
            summary = (
                await self.get_summary(
                    channel_id=channel.id,
                    user_id=user_id,
                )
            )

            summaries.append(
                summary
            )

            total_unread += (
                summary.unread_count
            )

        return (
            WorkspaceChannelUnreadListResponse(
                workspace_id=workspace_id,
                total_unread=total_unread,
                channels=summaries,
            )
        )


__all__ = [
    "WorkspaceChannelReadStateError",
    "WorkspaceChannelReadStateNotFoundError",
    "WorkspaceChannelReadStatePermissionError",
    "WorkspaceChannelReadStateService",
]