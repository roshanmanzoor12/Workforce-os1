from __future__ import annotations

import uuid

from sqlalchemy import (
    or_,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession

from .enums import FriendshipStatus
from .models import Friendship


def normalize_user_pair(
    first_user_id: uuid.UUID,
    second_user_id: uuid.UUID,
) -> tuple[
    uuid.UUID,
    uuid.UUID,
]:
    if first_user_id == second_user_id:
        raise ValueError(
            "A user cannot create a friendship "
            "with themselves."
        )

    ordered = sorted(
        (
            first_user_id,
            second_user_id,
        ),
        key=lambda value: value.int,
    )

    return (
        ordered[0],
        ordered[1],
    )


class FriendshipRepository:
    async def get_by_id(
        self,
        session: AsyncSession,
        *,
        friendship_id: uuid.UUID,
    ) -> Friendship | None:
        result = await session.execute(
            select(
                Friendship
            ).where(
                Friendship.id
                == friendship_id
            )
        )

        return result.scalar_one_or_none()

    async def get_between_users(
        self,
        session: AsyncSession,
        *,
        first_user_id: uuid.UUID,
        second_user_id: uuid.UUID,
    ) -> Friendship | None:
        (
            user_low_id,
            user_high_id,
        ) = normalize_user_pair(
            first_user_id,
            second_user_id,
        )

        result = await session.execute(
            select(
                Friendship
            ).where(
                Friendship.user_low_id
                == user_low_id,
                Friendship.user_high_id
                == user_high_id,
            )
        )

        return result.scalar_one_or_none()

    async def create_pending(
        self,
        session: AsyncSession,
        *,
        requester_user_id: uuid.UUID,
        target_user_id: uuid.UUID,
    ) -> Friendship:
        (
            user_low_id,
            user_high_id,
        ) = normalize_user_pair(
            requester_user_id,
            target_user_id,
        )

        friendship = Friendship(
            user_low_id=user_low_id,
            user_high_id=user_high_id,
            requested_by_user_id=(
                requester_user_id
            ),
            status=FriendshipStatus.PENDING,
        )

        session.add(
            friendship
        )

        await session.flush()

        return friendship

    async def list_for_user(
        self,
        session: AsyncSession,
        *,
        user_id: uuid.UUID,
        status: FriendshipStatus | None = None,
    ) -> list[Friendship]:
        statement = (
            select(
                Friendship
            )
            .where(
                or_(
                    Friendship.user_low_id
                    == user_id,
                    Friendship.user_high_id
                    == user_id,
                )
            )
            .order_by(
                Friendship.updated_at.desc()
            )
        )

        if status is not None:
            statement = statement.where(
                Friendship.status
                == status
            )

        result = await session.execute(
            statement
        )

        return list(
            result.scalars().all()
        )

    async def delete(
        self,
        session: AsyncSession,
        *,
        friendship: Friendship,
    ) -> None:
        await session.delete(
            friendship
        )

        await session.flush()


__all__ = [
    "FriendshipRepository",
    "normalize_user_pair",
]