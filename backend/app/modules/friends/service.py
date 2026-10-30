from __future__ import annotations

import uuid
from datetime import (
    datetime,
    timezone,
)

from sqlalchemy.ext.asyncio import AsyncSession

from .enums import FriendshipStatus
from .models import Friendship
from .repository import (
    FriendshipRepository,
)


class FriendshipError(
    ValueError
):
    pass


class FriendshipNotFoundError(
    FriendshipError
):
    pass


class FriendshipConflictError(
    FriendshipError
):
    pass


class FriendshipPermissionError(
    FriendshipError
):
    pass


class FriendshipService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        repository: FriendshipRepository | None = None,
    ) -> None:
        self.session = session

        self.repository = (
            repository
            or FriendshipRepository()
        )

    async def send_request(
        self,
        *,
        requester_user_id: uuid.UUID,
        target_user_id: uuid.UUID,
    ) -> Friendship:
        if (
            requester_user_id
            == target_user_id
        ):
            raise FriendshipConflictError(
                "A user cannot send a friend "
                "request to themselves."
            )

        existing = (
            await self.repository
            .get_between_users(
                self.session,
                first_user_id=(
                    requester_user_id
                ),
                second_user_id=(
                    target_user_id
                ),
            )
        )

        if existing is not None:
            if (
                existing.status
                == FriendshipStatus.ACCEPTED
            ):
                raise FriendshipConflictError(
                    "Users are already friends."
                )

            if (
                existing.status
                == FriendshipStatus.BLOCKED
            ):
                raise FriendshipPermissionError(
                    "Friend request is not allowed."
                )

            raise FriendshipConflictError(
                "A pending friend request "
                "already exists."
            )

        return await self.repository.create_pending(
            self.session,
            requester_user_id=(
                requester_user_id
            ),
            target_user_id=(
                target_user_id
            ),
        )

    async def accept_request(
        self,
        *,
        friendship_id: uuid.UUID,
        current_user_id: uuid.UUID,
    ) -> Friendship:
        friendship = (
            await self.repository.get_by_id(
                self.session,
                friendship_id=friendship_id,
            )
        )

        if friendship is None:
            raise FriendshipNotFoundError(
                "Friend request not found."
            )

        self._require_participant(
            friendship,
            current_user_id,
        )

        if (
            friendship.status
            != FriendshipStatus.PENDING
        ):
            raise FriendshipConflictError(
                "Friend request is not pending."
            )

        if (
            friendship.requested_by_user_id
            == current_user_id
        ):
            raise FriendshipPermissionError(
                "Requester cannot accept their "
                "own friend request."
            )

        friendship.status = (
            FriendshipStatus.ACCEPTED
        )

        friendship.accepted_at = (
            datetime.now(
                timezone.utc
            )
        )

        friendship.blocked_at = None

        await self.session.flush()

        return friendship

    async def reject_request(
        self,
        *,
        friendship_id: uuid.UUID,
        current_user_id: uuid.UUID,
    ) -> None:
        friendship = (
            await self.repository.get_by_id(
                self.session,
                friendship_id=friendship_id,
            )
        )

        if friendship is None:
            raise FriendshipNotFoundError(
                "Friend request not found."
            )

        self._require_participant(
            friendship,
            current_user_id,
        )

        if (
            friendship.status
            != FriendshipStatus.PENDING
        ):
            raise FriendshipConflictError(
                "Friend request is not pending."
            )

        if (
            friendship.requested_by_user_id
            == current_user_id
        ):
            raise FriendshipPermissionError(
                "Requester cannot reject their "
                "own request."
            )

        await self.repository.delete(
            self.session,
            friendship=friendship,
        )

    async def block_user(
        self,
        *,
        current_user_id: uuid.UUID,
        target_user_id: uuid.UUID,
    ) -> Friendship:
        if (
            current_user_id
            == target_user_id
        ):
            raise FriendshipConflictError(
                "A user cannot block themselves."
            )

        friendship = (
            await self.repository
            .get_between_users(
                self.session,
                first_user_id=current_user_id,
                second_user_id=target_user_id,
            )
        )

        if friendship is None:
            friendship = (
                await self.repository
                .create_pending(
                    self.session,
                    requester_user_id=(
                        current_user_id
                    ),
                    target_user_id=(
                        target_user_id
                    ),
                )
            )

        friendship.status = (
            FriendshipStatus.BLOCKED
        )

        friendship.requested_by_user_id = (
            current_user_id
        )

        friendship.accepted_at = None

        friendship.blocked_at = (
            datetime.now(
                timezone.utc
            )
        )

        await self.session.flush()

        return friendship

    async def unblock_user(
        self,
        *,
        current_user_id: uuid.UUID,
        target_user_id: uuid.UUID,
    ) -> None:
        friendship = (
            await self.repository
            .get_between_users(
                self.session,
                first_user_id=current_user_id,
                second_user_id=target_user_id,
            )
        )

        if friendship is None:
            raise FriendshipNotFoundError(
                "Blocked relationship not found."
            )

        if (
            friendship.status
            != FriendshipStatus.BLOCKED
        ):
            raise FriendshipConflictError(
                "Relationship is not blocked."
            )

        if (
            friendship.requested_by_user_id
            != current_user_id
        ):
            raise FriendshipPermissionError(
                "Only the blocking user can "
                "remove this block."
            )

        await self.repository.delete(
            self.session,
            friendship=friendship,
        )

    async def list_relationships(
        self,
        *,
        user_id: uuid.UUID,
        status: FriendshipStatus | None = None,
    ) -> list[Friendship]:
        return await self.repository.list_for_user(
            self.session,
            user_id=user_id,
            status=status,
        )

    async def are_friends(
        self,
        *,
        first_user_id: uuid.UUID,
        second_user_id: uuid.UUID,
    ) -> bool:
        friendship = (
            await self.repository
            .get_between_users(
                self.session,
                first_user_id=first_user_id,
                second_user_id=second_user_id,
            )
        )

        return (
            friendship is not None
            and friendship.status
            == FriendshipStatus.ACCEPTED
        )

    @staticmethod
    def _require_participant(
        friendship: Friendship,
        user_id: uuid.UUID,
    ) -> None:
        if user_id not in (
            friendship.user_low_id,
            friendship.user_high_id,
        ):
            raise FriendshipPermissionError(
                "User is not part of this "
                "friendship."
            )


__all__ = [
    "FriendshipConflictError",
    "FriendshipError",
    "FriendshipNotFoundError",
    "FriendshipPermissionError",
    "FriendshipService",
]