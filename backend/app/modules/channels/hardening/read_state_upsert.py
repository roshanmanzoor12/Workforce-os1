from __future__ import annotations

import uuid
from datetime import (
    datetime,
    timezone,
)

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.channels.read_state_models import (
    WorkspaceChannelReadState,
)


def utcnow() -> datetime:
    return datetime.now(
        timezone.utc
    )


class ChannelReadStateUpserter:
    """
    Atomic PostgreSQL UPSERT for workspace channel read state.

    Phase 16C used a get-then-insert pattern.  Concurrent clients can both
    observe no row and race on the unique channel/user constraint.

    ON CONFLICT removes that race.
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def upsert(
        self,
        *,
        workspace_id: uuid.UUID,
        channel_id: uuid.UUID,
        user_id: uuid.UUID,
        last_read_message_id: uuid.UUID | None,
        read_at: datetime | None = None,
    ) -> WorkspaceChannelReadState:
        timestamp = (
            read_at
            if read_at is not None
            else utcnow()
        )

        values = {
            "id": uuid.uuid4(),
            "workspace_id": workspace_id,
            "channel_id": channel_id,
            "user_id": user_id,
            "last_read_message_id": (
                last_read_message_id
            ),
            "last_read_at": timestamp,
            "created_at": timestamp,
            "updated_at": timestamp,
        }

        statement = insert(
            WorkspaceChannelReadState
        ).values(
            **values
        )

        statement = (
            statement
            .on_conflict_do_update(
                index_elements=[
                    WorkspaceChannelReadState.channel_id,
                    WorkspaceChannelReadState.user_id,
                ],
                set_={
                    "workspace_id":
                        workspace_id,

                    "last_read_message_id":
                        last_read_message_id,

                    "last_read_at":
                        timestamp,

                    "updated_at":
                        timestamp,
                },
            )
            .returning(
                WorkspaceChannelReadState
            )
        )

        result = await self.session.execute(
            statement
        )

        state = result.scalar_one()

        return state

    async def upsert_and_flush(
        self,
        *,
        workspace_id: uuid.UUID,
        channel_id: uuid.UUID,
        user_id: uuid.UUID,
        last_read_message_id: uuid.UUID | None,
        read_at: datetime | None = None,
    ) -> WorkspaceChannelReadState:
        state = await self.upsert(
            workspace_id=workspace_id,
            channel_id=channel_id,
            user_id=user_id,
            last_read_message_id=last_read_message_id,
            read_at=read_at,
        )

        await self.session.flush()

        return state