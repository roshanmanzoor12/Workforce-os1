from __future__ import annotations

from functools import partial
from typing import Literal
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.core.database import get_control_db
from app.core.exceptions import StorageError
from app.core.storage import download_bytes, upload_bytes
from app.modules.auth.models import AuthIdentity, User
from app.modules.auth.permissions import get_current_verified_user
from app.modules.auth.schemas import UserPublic
from .avatar_images import MAX_UPLOAD_BYTES, PRESET_IDS, crop_profile_photo, preset_image

router = APIRouter(prefix="/personal", tags=["Profile photos"])
AVATAR_ROOT = "/api/v1/personal/avatars"


class AvatarSelection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source: Literal["google", "preset", "none"]
    preset_id: str | None = None


class AvatarResponse(BaseModel):
    user: UserPublic


async def save_avatar(db: AsyncSession, user: User, source: str,
                      url: str | None) -> AvatarResponse:
    user.avatar_source = source
    user.avatar_url = url
    await db.commit()
    await db.refresh(user)
    return AvatarResponse(user=UserPublic.model_validate(user))


@router.post("/profile/avatar/upload", response_model=AvatarResponse)
async def upload_avatar(
    response: Response,
    file: UploadFile = File(...),
    zoom: float = Form(1, ge=1, le=3),
    x: float = Form(0, ge=-1, le=1),
    y: float = Form(0, ge=-1, le=1),
    db: AsyncSession = Depends(get_control_db),
    user: User = Depends(get_current_verified_user),
):
    response.headers["Cache-Control"] = "private, no-store"
    try:
        data = await file.read(MAX_UPLOAD_BYTES + 1)
    finally:
        await file.close()
    try:
        encoded = await run_in_threadpool(crop_profile_photo, data, zoom, x, y)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    version = uuid.uuid4()
    key = f"profile-avatars/{user.id}/{version}.webp"
    try:
        await run_in_threadpool(partial(upload_bytes, object_key=key, data=encoded,
                                       content_type="image/webp"))
    except StorageError as exc:
        raise HTTPException(503, "Photo storage is unavailable. Your previous photo is unchanged; retry shortly.") from exc
    return await save_avatar(db, user, "upload", f"{AVATAR_ROOT}/uploads/{user.id}/{version}.webp")


@router.post("/profile/avatar", response_model=AvatarResponse)
async def choose_avatar(
    payload: AvatarSelection, response: Response,
    db: AsyncSession = Depends(get_control_db),
    user: User = Depends(get_current_verified_user),
):
    response.headers["Cache-Control"] = "private, no-store"
    if payload.source == "none":
        return await save_avatar(db, user, "none", None)
    if payload.source == "preset":
        if payload.preset_id not in PRESET_IDS:
            raise HTTPException(422, "Choose one of the available avatars.")
        return await save_avatar(db, user, "preset", f"{AVATAR_ROOT}/presets/{payload.preset_id}.webp")
    identity = (await db.execute(select(AuthIdentity).where(
        AuthIdentity.user_id == user.id, AuthIdentity.provider == "google",
    ).order_by(AuthIdentity.created_at.desc()))).scalars().first()
    if identity is None or not identity.provider_avatar_url:
        raise HTTPException(409, "No Google photo is available. Sign in with Google, then try again.")
    return await save_avatar(db, user, "google", identity.provider_avatar_url)


# Profile photos are public image resources, like the provider images already
# returned by the user directory. Mutations above always require authentication.
@router.get("/avatars/presets/{preset_id}.webp")
async def get_preset(preset_id: str):
    if preset_id not in PRESET_IDS:
        raise HTTPException(404, "Avatar not found.")
    data = await run_in_threadpool(preset_image, preset_id)
    return Response(data, media_type="image/webp", headers={
        "Cache-Control": "public, max-age=86400", "X-Content-Type-Options": "nosniff",
    })


@router.get("/avatars/uploads/{user_id}/{version}.webp")
async def get_uploaded_avatar(user_id: uuid.UUID, version: uuid.UUID):
    # Both path values are parsed as UUIDs; callers cannot name arbitrary keys.
    try:
        data = await run_in_threadpool(partial(
            download_bytes, object_key=f"profile-avatars/{user_id}/{version}.webp"))
    except StorageError as exc:
        raise HTTPException(404, "Photo unavailable.") from exc
    return Response(data, media_type="image/webp", headers={
        "Cache-Control": "public, max-age=31536000, immutable",
        "X-Content-Type-Options": "nosniff",
    })
