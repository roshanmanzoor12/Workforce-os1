from __future__ import annotations

import uuid

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.core.database import (
    get_control_db,
)
from app.modules.auth.models import User
from app.modules.auth.permissions import (
    get_current_verified_user,
)

from .message_pagination_service import (
    MessagePaginationService,
)
from .pagination_schemas import (
    ChatMessagePagePublic,
)
from .schemas import (
    ChatMessagePublic,
)
from .service import (
    ChatPermissionError,
    ConversationNotFoundError,
)


router = APIRouter(
    prefix="/chat",
    tags=[
        "Chat",
    ],
)


@router.get(
    "/{conversation_id}/messages-page",
    response_model=ChatMessagePagePublic,
)
async def list_message_page(
    conversation_id: uuid.UUID,
    cursor: str | None = Query(
        default=None,
        max_length=1000,
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
    ),
    session: AsyncSession = Depends(
        get_control_db
    ),
    user: User = Depends(
        get_current_verified_user
    ),
) -> ChatMessagePagePublic:
    service = MessagePaginationService(
        session
    )

    try:
        page = await service.list_page(
            conversation_id=conversation_id,
            user_id=user.id,
            limit=limit,
            cursor=cursor,
        )

    except ConversationNotFoundError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=str(
                exc
            ),
        ) from exc

    except ChatPermissionError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=str(
                exc
            ),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=str(
                exc
            ),
        ) from exc

    return ChatMessagePagePublic(
        items=[
            ChatMessagePublic.model_validate(
                message
            )
            for message in page.items
        ],
        next_cursor=page.next_cursor,
        has_more=page.has_more,
    )


__all__ = [
    "router",
]