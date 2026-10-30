from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_control_db
from app.modules.auth.models import AuthIdentity, User
from app.modules.auth.permissions import get_current_verified_user
from app.modules.auth.schemas import SignupRequest, UserPublic
from app.modules.notifications.router import router as notifications_router

router = APIRouter(tags=["Personal account"])
# This supplies the workspace path parameter required by tenant authorization.
# The existing notification service still enforces active membership and scope.
router.include_router(notifications_router, prefix="/workspaces/{workspace_id}")


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    username: str = Field(min_length=3, max_length=64)
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    avatar_url: str | None = Field(default=None, max_length=2048)

    @field_validator("username")
    @classmethod
    def username_policy(cls, value: str) -> str:
        return SignupRequest.validate_username(value)

    @field_validator("avatar_url")
    @classmethod
    def avatar_policy(cls, value: str | None) -> str | None:
        if not value:
            return None
        from urllib.parse import urlsplit
        parsed = urlsplit(value)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("Avatar must be an HTTPS image URL without embedded credentials.")
        return value

    @field_validator("first_name", "last_name")
    @classmethod
    def empty_name(cls, value: str | None) -> str | None:
        return value or None


class IdentityPublic(BaseModel):
    provider: str
    email: str | None
    connected_at: datetime
    last_authenticated_at: datetime | None


class AccountResponse(BaseModel):
    user: UserPublic
    has_password: bool
    last_login_at: datetime | None
    password_changed_at: datetime | None
    identities: list[IdentityPublic]
    google_avatar_url: str | None = None


async def account_response(db: AsyncSession, user: User) -> AccountResponse:
    identities = (await db.execute(
        select(AuthIdentity).where(AuthIdentity.user_id == user.id)
        .order_by(AuthIdentity.created_at.desc())
    )).scalars().all()
    return AccountResponse(
        user=UserPublic.model_validate(user),
        google_avatar_url=next((item.provider_avatar_url for item in identities
                                if item.provider == "google" and item.provider_avatar_url), None),
        has_password=bool(user.password_hash),
        last_login_at=user.last_login_at,
        password_changed_at=user.password_changed_at,
        identities=[IdentityPublic(
            provider=item.provider, email=item.provider_email,
            connected_at=item.created_at,
            last_authenticated_at=item.last_authenticated_at,
        ) for item in identities],
    )


@router.get("/personal/profile", response_model=AccountResponse)
async def get_profile(response: Response, db: AsyncSession = Depends(get_control_db),
                      user: User = Depends(get_current_verified_user)):
    response.headers["Cache-Control"] = "private, no-store"
    return await account_response(db, user)


@router.patch("/personal/profile", response_model=AccountResponse)
async def update_profile(payload: ProfileUpdate, response: Response,
                         db: AsyncSession = Depends(get_control_db),
                         user: User = Depends(get_current_verified_user)):
    response.headers["Cache-Control"] = "private, no-store"
    # The authenticated user is the only update target. Email, password,
    # verification flags and workspace roles are deliberately not accepted.
    owner_id: uuid.UUID = user.id
    existing = (await db.execute(select(User.id).where(
        User.username == payload.username, User.id != owner_id,
    ))).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(409, "This username is already in use.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    if "avatar_url" in payload.model_fields_set:
        user.avatar_source = "url" if payload.avatar_url else "none"
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(409, "Profile conflicts with an existing account. Try a different username.") from exc
    await db.refresh(user)
    return await account_response(db, user)

from .avatar_router import router as avatar_router
router.include_router(avatar_router)
