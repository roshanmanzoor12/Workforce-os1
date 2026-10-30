from __future__ import annotations

import uuid

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import (
    get_control_db,
)
from app.modules.auth.models import User
from app.modules.auth.permissions import (
    get_current_verified_user,
)

from .enums import FriendshipStatus
from .schemas import (
    FriendshipListResponse,
    FriendshipPublic,
)
from .service import (
    FriendshipConflictError,
    FriendshipNotFoundError,
    FriendshipPermissionError,
    FriendshipService,
)

from sqlalchemy import or_, select
from app.modules.auth.models import User
from .schemas import FriendUserPublic
from sqlalchemy import String

router = APIRouter(
    prefix="/friends",
    tags=[
        "Friends",
    ],
)


def translate_friendship_error(
    exc: Exception,
) -> HTTPException:
    if isinstance(
        exc,
        FriendshipNotFoundError,
    ):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    if isinstance(
        exc,
        FriendshipPermissionError,
    ):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )

    if isinstance(
        exc,
        FriendshipConflictError,
    ):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(exc),
    )


@router.post(
    "/requests/{target_user_id}",
    response_model=FriendshipPublic,
    status_code=status.HTTP_201_CREATED,
)
async def send_friend_request(
    target_user_id: uuid.UUID,
    session: AsyncSession = Depends(
        get_control_db
    ),
    user: User = Depends(
        get_current_verified_user
    ),
) -> FriendshipPublic:
    service = FriendshipService(
        session
    )

    try:
        friendship = (
            await service.send_request(
                requester_user_id=user.id,
                target_user_id=target_user_id,
            )
        )

        await session.commit()

        return FriendshipPublic.model_validate(
            friendship
        )

    except (
        FriendshipConflictError,
        FriendshipPermissionError,
        FriendshipNotFoundError,
    ) as exc:
        await session.rollback()

        raise translate_friendship_error(
            exc
        ) from exc


@router.post(
    "/requests/{friendship_id}/accept",
    response_model=FriendshipPublic,
)
async def accept_friend_request(
    friendship_id: uuid.UUID,
    session: AsyncSession = Depends(
        get_control_db
    ),
    user: User = Depends(
        get_current_verified_user
    ),
) -> FriendshipPublic:
    service = FriendshipService(
        session
    )

    try:
        friendship = (
            await service.accept_request(
                friendship_id=friendship_id,
                current_user_id=user.id,
            )
        )

        await session.commit()

        return FriendshipPublic.model_validate(
            friendship
        )

    except (
        FriendshipConflictError,
        FriendshipPermissionError,
        FriendshipNotFoundError,
    ) as exc:
        await session.rollback()

        raise translate_friendship_error(
            exc
        ) from exc


@router.delete(
    "/requests/{friendship_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def reject_friend_request(
    friendship_id: uuid.UUID,
    session: AsyncSession = Depends(
        get_control_db
    ),
    user: User = Depends(
        get_current_verified_user
    ),
) -> Response:
    service = FriendshipService(
        session
    )

    try:
        await service.reject_request(
            friendship_id=friendship_id,
            current_user_id=user.id,
        )

        await session.commit()

        return Response(
            status_code=(
                status.HTTP_204_NO_CONTENT
            )
        )

    except (
        FriendshipConflictError,
        FriendshipPermissionError,
        FriendshipNotFoundError,
    ) as exc:
        await session.rollback()

        raise translate_friendship_error(
            exc
        ) from exc


@router.post(
    "/blocks/{target_user_id}",
    response_model=FriendshipPublic,
)
async def block_user(
    target_user_id: uuid.UUID,
    session: AsyncSession = Depends(
        get_control_db
    ),
    user: User = Depends(
        get_current_verified_user
    ),
) -> FriendshipPublic:
    service = FriendshipService(
        session
    )

    try:
        friendship = (
            await service.block_user(
                current_user_id=user.id,
                target_user_id=target_user_id,
            )
        )

        await session.commit()

        return FriendshipPublic.model_validate(
            friendship
        )

    except (
        FriendshipConflictError,
        FriendshipPermissionError,
        FriendshipNotFoundError,
    ) as exc:
        await session.rollback()

        raise translate_friendship_error(
            exc
        ) from exc


@router.delete(
    "/blocks/{target_user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def unblock_user(
    target_user_id: uuid.UUID,
    session: AsyncSession = Depends(
        get_control_db
    ),
    user: User = Depends(
        get_current_verified_user
    ),
) -> Response:
    service = FriendshipService(
        session
    )

    try:
        await service.unblock_user(
            current_user_id=user.id,
            target_user_id=target_user_id,
        )

        await session.commit()

        return Response(
            status_code=(
                status.HTTP_204_NO_CONTENT
            )
        )

    except (
        FriendshipConflictError,
        FriendshipPermissionError,
        FriendshipNotFoundError,
    ) as exc:
        await session.rollback()

        raise translate_friendship_error(
            exc
        ) from exc


@router.get(
    "",
    response_model=FriendshipListResponse,
)
async def list_friendships(
    relationship_status: FriendshipStatus | None = Query(
        default=None,
        alias="status",
    ),
    session: AsyncSession = Depends(
        get_control_db
    ),
    user: User = Depends(
        get_current_verified_user
    ),
) -> FriendshipListResponse:
    service = FriendshipService(
        session
    )

    items = (
        await service.list_relationships(
            user_id=user.id,
            status=relationship_status,
        )
    )

    return FriendshipListResponse(
        items=[
            FriendshipPublic.model_validate(
                item
            )
            for item in items
        ]
    )

@router.get(
    "/lookup",
    response_model=FriendUserPublic,
)
async def lookup_friend(
    identifier: str = Query(
        min_length=3,
        max_length=128,
    ),
    session: AsyncSession = Depends(get_control_db),
    user: User = Depends(get_current_verified_user),
) -> FriendUserPublic:
    value = identifier.strip().lstrip("@").lower()

    statement = select(User).where(
        User.is_active.is_(True),
        User.is_email_verified.is_(True),
        or_(
            User.username == value,
            User.id.cast(String) == value,
        ),
    )

    result = await session.execute(statement)
    target = result.scalar_one_or_none()

    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    if target.id == user.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You cannot add yourself.",
        )

    return FriendUserPublic.model_validate(target)