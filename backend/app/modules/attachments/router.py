from __future__ import annotations

import uuid

from fastapi import (
    APIRouter,
    Depends,
    Response,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_control_db
from app.modules.attachments.limits import (
    get_attachment_limit_bytes,
    get_attachment_limit_mb,
)
from app.modules.attachments.schemas import (
    AttachmentCompleteRequest,
    AttachmentDownloadResponse,
    AttachmentPlanLimitResponse,
    AttachmentPrepareRequest,
    AttachmentPrepareResponse,
    AttachmentResponse,
)
from app.modules.attachments.service import (
    AttachmentService,
)
from app.modules.attachments.storage import (
    get_attachment_storage,
)
from app.modules.auth.permissions import (
    get_current_verified_user,
)


router = APIRouter(
    prefix="/attachments",
    tags=["attachments"],
)


def _user_id(user: object) -> uuid.UUID:
    value = getattr(user, "id")

    if isinstance(value, uuid.UUID):
        return value

    return uuid.UUID(str(value))


def _user_plan(user: object) -> str:
    plan = getattr(
        user,
        "plan_code",
        None,
    )

    if plan:
        return str(plan).upper()

    subscription = getattr(
        user,
        "subscription",
        None,
    )

    if subscription is not None:
        subscription_plan = getattr(
            subscription,
            "plan_code",
            None,
        )

        if subscription_plan:
            return str(
                subscription_plan
            ).upper()

        plan_object = getattr(
            subscription,
            "plan",
            None,
        )

        if plan_object is not None:
            code = getattr(
                plan_object,
                "code",
                None,
            )

            if code:
                return str(code).upper()

    return "FREE"


def _service(
    db: AsyncSession,
) -> AttachmentService:
    return AttachmentService(
        db=db,
        storage=get_attachment_storage(),
    )


@router.get(
    "/limits",
    response_model=AttachmentPlanLimitResponse,
)
async def attachment_limits(
    current_user=Depends(
        get_current_verified_user
    ),
) -> AttachmentPlanLimitResponse:
    plan = _user_plan(current_user)

    return AttachmentPlanLimitResponse(
        plan=plan,
        max_size_bytes=(
            get_attachment_limit_bytes(plan)
        ),
        max_size_mb=(
            get_attachment_limit_mb(plan)
        ),
    )


@router.post(
    "/prepare",
    response_model=AttachmentPrepareResponse,
    status_code=status.HTTP_201_CREATED,
)
async def prepare_attachment(
    payload: AttachmentPrepareRequest,
    db: AsyncSession = Depends(
        get_control_db
    ),
    current_user=Depends(
        get_current_verified_user
    ),
) -> AttachmentPrepareResponse:
    user_id = _user_id(current_user)
    plan = _user_plan(current_user)

    attachment, upload_url, max_size = (
        await _service(db).prepare(
            user_id=user_id,
            plan_code=plan,
            request=payload,
        )
    )

    return AttachmentPrepareResponse(
        attachment_id=attachment.id,
        upload_url=upload_url,
        expires_in_seconds=900,
        max_size_bytes=max_size,
    )


@router.post(
    "/{attachment_id}/complete",
    response_model=AttachmentResponse,
)
async def complete_attachment(
    attachment_id: uuid.UUID,
    payload: AttachmentCompleteRequest,
    db: AsyncSession = Depends(
        get_control_db
    ),
    current_user=Depends(
        get_current_verified_user
    ),
) -> AttachmentResponse:
    attachment = await _service(db).complete(
        attachment_id=attachment_id,
        user_id=_user_id(current_user),
        checksum_sha256=payload.checksum_sha256,
    )

    return AttachmentResponse.model_validate(
        attachment
    )


@router.get(
    "/{attachment_id}",
    response_model=AttachmentResponse,
)
async def get_attachment(
    attachment_id: uuid.UUID,
    db: AsyncSession = Depends(
        get_control_db
    ),
    current_user=Depends(
        get_current_verified_user
    ),
) -> AttachmentResponse:
    service = _service(db)

    attachment = await service.get_attachment(
        attachment_id=attachment_id
    )

    await service.assert_attachment_access(
        attachment=attachment,
        user_id=_user_id(current_user),
    )

    return AttachmentResponse.model_validate(
        attachment
    )


@router.post(
    "/{attachment_id}/download",
    response_model=AttachmentDownloadResponse,
)
async def download_attachment(
    attachment_id: uuid.UUID,
    db: AsyncSession = Depends(
        get_control_db
    ),
    current_user=Depends(
        get_current_verified_user
    ),
) -> AttachmentDownloadResponse:
    attachment, download_url, expiry = (
        await _service(db).create_download_url(
            attachment_id=attachment_id,
            user_id=_user_id(current_user),
        )
    )

    return AttachmentDownloadResponse(
        attachment_id=attachment.id,
        download_url=download_url,
        expires_in_seconds=expiry,
    )


@router.delete(
    "/{attachment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_attachment(
    attachment_id: uuid.UUID,
    db: AsyncSession = Depends(
        get_control_db
    ),
    current_user=Depends(
        get_current_verified_user
    ),
) -> Response:
    await _service(db).delete(
        attachment_id=attachment_id,
        user_id=_user_id(current_user),
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )

