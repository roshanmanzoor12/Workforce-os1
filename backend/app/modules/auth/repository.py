from __future__ import annotations

import uuid
from datetime import datetime
from typing import Sequence

from sqlalchemy import and_, delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.auth.models import (
    AuthIdentity,
    EmailVerificationChallenge,
    PasswordResetChallenge,
    RefreshSession,
    User,
)


# =========================================================
# AUTH REPOSITORY
# =========================================================


class AuthRepository:
    """
    Database-access layer for global WorkforceOS authentication.

    This repository only works with the control database.

    Responsibilities:
    - users
    - auth identities
    - refresh sessions
    - email verification challenges
    - password reset challenges

    It must NOT:
    - hash passwords
    - create JWTs
    - generate OTPs
    - send email
    - decide authentication policy
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    # =====================================================
    # USERS
    # =====================================================

    async def get_user_by_id(
        self,
        user_id: uuid.UUID,
        *,
        include_relationships: bool = False,
    ) -> User | None:
        statement = select(User).where(
            User.id == user_id
        )

        if include_relationships:
            statement = statement.options(
                selectinload(
                    User.auth_identities
                ),
                selectinload(
                    User.refresh_sessions
                ),
            )

        result = await self.session.execute(
            statement
        )

        return result.scalar_one_or_none()

    async def get_user_by_email(
        self,
        email: str,
    ) -> User | None:
        result = await self.session.execute(
            select(User).where(
                User.email == email
            )
        )

        return result.scalar_one_or_none()

    async def get_user_by_username(
        self,
        username: str,
    ) -> User | None:
        result = await self.session.execute(
            select(User).where(
                User.username == username
            )
        )

        return result.scalar_one_or_none()

    async def get_user_by_identifier(
        self,
        identifier: str,
    ) -> User | None:
        result = await self.session.execute(
            select(User).where(
                or_(
                    User.email == identifier,
                    User.username == identifier,
                )
            )
        )

        return result.scalar_one_or_none()

    async def email_exists(
        self,
        email: str,
    ) -> bool:
        result = await self.session.execute(
            select(
                func.count(User.id)
            ).where(
                User.email == email
            )
        )

        return bool(
            result.scalar_one()
        )

    async def username_exists(
        self,
        username: str,
    ) -> bool:
        result = await self.session.execute(
            select(
                func.count(User.id)
            ).where(
                User.username == username
            )
        )

        return bool(
            result.scalar_one()
        )

    async def create_user(
        self,
        *,
        email: str,
        username: str,
        password_hash: str | None,
        first_name: str | None = None,
        last_name: str | None = None,
        avatar_url: str | None = None,
        is_email_verified: bool = False,
        email_verified_at: datetime | None = None,
    ) -> User:
        user = User(
            email=email,
            username=username,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            avatar_url=avatar_url,
            is_email_verified=is_email_verified,
            email_verified_at=email_verified_at,
        )

        self.session.add(
            user
        )

        await self.session.flush()

        await self.session.refresh(
            user
        )

        return user

    async def update_user_password(
        self,
        user: User,
        *,
        password_hash: str,
        changed_at: datetime,
    ) -> User:
        user.password_hash = password_hash
        user.password_changed_at = changed_at

        await self.session.flush()

        return user

    async def mark_email_verified(
        self,
        user: User,
        *,
        verified_at: datetime,
    ) -> User:
        user.is_email_verified = True
        user.email_verified_at = verified_at

        await self.session.flush()

        return user

    async def mark_user_email_verified(
        self,
        user: User,
        *,
        verified_at: datetime,
    ) -> User:
        return await self.mark_email_verified(
            user,
            verified_at=verified_at,
        )

    async def update_last_login(
        self,
        user: User,
        *,
        logged_in_at: datetime,
    ) -> User:
        user.last_login_at = logged_in_at
        user.failed_login_attempts = 0

        await self.session.flush()

        return user

    async def increment_failed_login_attempts(
        self,
        user: User,
    ) -> int:
        user.failed_login_attempts += 1

        await self.session.flush()

        return user.failed_login_attempts

    async def reset_failed_login_attempts(
        self,
        user: User,
    ) -> None:
        user.failed_login_attempts = 0

        await self.session.flush()

    async def lock_user(
        self,
        user: User,
        *,
        locked_at: datetime,
        reason: str | None = None,
    ) -> User:
        user.is_locked = True
        user.locked_at = locked_at
        user.locked_reason = reason

        await self.session.flush()

        return user

    async def unlock_user(
        self,
        user: User,
    ) -> User:
        user.is_locked = False
        user.locked_at = None
        user.locked_reason = None
        user.failed_login_attempts = 0

        await self.session.flush()

        return user

    async def set_user_active(
        self,
        user: User,
        *,
        active: bool,
    ) -> User:
        user.is_active = active

        await self.session.flush()

        return user

    # =====================================================
    # AUTH IDENTITIES
    # =====================================================

    async def get_auth_identity_by_id(
        self,
        identity_id: uuid.UUID,
    ) -> AuthIdentity | None:
        result = await self.session.execute(
            select(AuthIdentity).where(
                AuthIdentity.id == identity_id
            )
        )

        return result.scalar_one_or_none()

    async def get_auth_identity(
        self,
        *,
        provider: str,
        provider_subject: str | None = None,
        provider_user_id: str | None = None,
    ) -> AuthIdentity | None:
        subject = (
            provider_user_id
            if provider_user_id is not None
            else provider_subject
        )

        if not subject:
            raise ValueError(
                "provider_subject/provider_user_id is required."
            )

        result = await self.session.execute(
            select(AuthIdentity).where(
                and_(
                    AuthIdentity.provider == provider,
                    AuthIdentity.provider_subject == subject,
                )
            )
        )

        return result.scalar_one_or_none()

    async def get_user_provider_identity(
        self,
        *,
        user_id: uuid.UUID,
        provider: str,
    ) -> AuthIdentity | None:
        result = await self.session.execute(
            select(AuthIdentity).where(
                and_(
                    AuthIdentity.user_id == user_id,
                    AuthIdentity.provider == provider,
                )
            )
        )

        return result.scalar_one_or_none()

    async def list_user_auth_identities(
        self,
        user_id: uuid.UUID,
    ) -> Sequence[AuthIdentity]:
        result = await self.session.execute(
            select(AuthIdentity)
            .where(
                AuthIdentity.user_id == user_id
            )
            .order_by(
                AuthIdentity.created_at.asc()
            )
        )

        return result.scalars().all()

    async def create_auth_identity(
        self,
        *,
        user_id: uuid.UUID,
        provider: str,
        provider_subject: str | None = None,
        provider_user_id: str | None = None,
        provider_email: str | None = None,
        provider_username: str | None = None,
        provider_avatar_url: str | None = None,
        provider_email_verified: bool | None = None,
        last_authenticated_at: datetime | None = None,
    ) -> AuthIdentity:
        subject = (
            provider_user_id
            if provider_user_id is not None
            else provider_subject
        )

        if not subject:
            raise ValueError(
                "provider_subject/provider_user_id is required."
            )

        identity = AuthIdentity(
            user_id=user_id,
            provider=provider,
            provider_subject=subject,
            provider_email=provider_email,
            provider_username=provider_username,
            provider_avatar_url=provider_avatar_url,
            provider_email_verified=provider_email_verified,
            last_authenticated_at=last_authenticated_at,
        )

        self.session.add(
            identity
        )

        await self.session.flush()

        await self.session.refresh(
            identity
        )

        return identity

    async def update_auth_identity_login(
        self,
        identity: AuthIdentity,
        *,
        last_authenticated_at: datetime,
        provider_email: str | None = None,
        provider_username: str | None = None,
        provider_avatar_url: str | None = None,
        provider_email_verified: bool | None = None,
    ) -> AuthIdentity:
        identity.last_authenticated_at = last_authenticated_at

        if provider_email is not None:
            identity.provider_email = provider_email

        if provider_username is not None:
            identity.provider_username = provider_username

        if provider_avatar_url is not None:
            identity.provider_avatar_url = provider_avatar_url

        if provider_email_verified is not None:
            identity.provider_email_verified = (
                provider_email_verified
            )

        await self.session.flush()

        return identity

    async def update_auth_identity(
        self,
        identity: AuthIdentity,
        *,
        provider_email: str | None = None,
        provider_username: str | None = None,
        provider_avatar_url: str | None = None,
        provider_email_verified: bool | None = None,
        last_authenticated_at: datetime | None = None,
    ) -> AuthIdentity:
        if last_authenticated_at is not None:
            identity.last_authenticated_at = (
                last_authenticated_at
            )

        if provider_email is not None:
            identity.provider_email = provider_email

        if provider_username is not None:
            identity.provider_username = provider_username

        if provider_avatar_url is not None:
            identity.provider_avatar_url = provider_avatar_url

        if provider_email_verified is not None:
            identity.provider_email_verified = (
                provider_email_verified
            )

        await self.session.flush()

        return identity

    async def delete_auth_identity(
        self,
        identity: AuthIdentity,
    ) -> None:
        await self.session.delete(
            identity
        )

        await self.session.flush()

    # =====================================================
    # REFRESH SESSIONS
    # =====================================================

    async def get_refresh_session_by_id(
        self,
        session_id: uuid.UUID,
    ) -> RefreshSession | None:
        result = await self.session.execute(
            select(RefreshSession).where(
                RefreshSession.id == session_id
            )
        )

        return result.scalar_one_or_none()

    async def get_refresh_session_by_jti(
        self,
        jti: str,
    ) -> RefreshSession | None:
        result = await self.session.execute(
            select(RefreshSession).where(
                RefreshSession.jti == jti
            )
        )

        return result.scalar_one_or_none()

    async def get_refresh_session_by_token_hash(
        self,
        token_hash: str,
    ) -> RefreshSession | None:
        result = await self.session.execute(
            select(RefreshSession).where(
                RefreshSession.token_hash == token_hash
            )
        )

        return result.scalar_one_or_none()

    async def create_refresh_session(
        self,
        *,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
        jti: str,
        token_hash: str,
        expires_at: datetime,
        device_name: str | None = None,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> RefreshSession:
        refresh_session = RefreshSession(
            id=session_id,
            user_id=user_id,
            jti=jti,
            token_hash=token_hash,
            expires_at=expires_at,
            device_name=device_name,
            user_agent=user_agent,
            ip_address=ip_address,
        )

        self.session.add(
            refresh_session
        )

        await self.session.flush()

        await self.session.refresh(
            refresh_session
        )

        return refresh_session

    async def list_user_refresh_sessions(
        self,
        user_id: uuid.UUID,
        *,
        include_revoked: bool = False,
    ) -> Sequence[RefreshSession]:
        statement = select(
            RefreshSession
        ).where(
            RefreshSession.user_id == user_id
        )

        if not include_revoked:
            statement = statement.where(
                RefreshSession.revoked_at.is_(
                    None
                )
            )

        statement = statement.order_by(
            RefreshSession.created_at.desc()
        )

        result = await self.session.execute(
            statement
        )

        return result.scalars().all()

    async def mark_refresh_session_used(
        self,
        session: RefreshSession,
        *,
        used_at: datetime,
    ) -> RefreshSession:
        session.last_used_at = used_at

        await self.session.flush()

        return session

    async def revoke_refresh_session(
        self,
        session: RefreshSession,
        *,
        revoked_at: datetime,
        reason: str | None = None,
    ) -> RefreshSession:
        if session.revoked_at is None:
            session.revoked_at = revoked_at
            session.revoke_reason = reason

            await self.session.flush()

        return session

    async def revoke_all_user_sessions(
        self,
        user_id: uuid.UUID,
        *,
        revoked_at: datetime,
        reason: str | None = None,
        exclude_session_id: uuid.UUID | None = None,
    ) -> int:
        conditions = [
            RefreshSession.user_id == user_id,
            RefreshSession.revoked_at.is_(None),
        ]

        if exclude_session_id is not None:
            conditions.append(
                RefreshSession.id != exclude_session_id
            )

        result = await self.session.execute(
            update(
                RefreshSession
            )
            .where(
                *conditions
            )
            .values(
                revoked_at=revoked_at,
                revoke_reason=reason,
            )
        )

        return int(
            result.rowcount or 0
        )

    async def mark_session_rotated(
        self,
        session: RefreshSession,
        *,
        rotated_at: datetime,
        replacement_session_id: uuid.UUID,
    ) -> RefreshSession:
        session.rotated_at = rotated_at
        session.replaced_by_session_id = (
            replacement_session_id
        )

        await self.session.flush()

        return session

    async def delete_expired_refresh_sessions(
        self,
        *,
        before: datetime,
    ) -> int:
        result = await self.session.execute(
            delete(
                RefreshSession
            ).where(
                RefreshSession.expires_at < before
            )
        )

        return int(
            result.rowcount or 0
        )

    # =====================================================
    # EMAIL VERIFICATION CHALLENGES
    # =====================================================

    async def create_email_verification_challenge(
        self,
        *,
        user_id: uuid.UUID,
        otp_hash: str,
        expires_at: datetime,
        max_attempts: int,
        sent_to_email: str,
    ) -> EmailVerificationChallenge:
        challenge = EmailVerificationChallenge(
            user_id=user_id,
            otp_hash=otp_hash,
            expires_at=expires_at,
            max_attempts=max_attempts,
            sent_to_email=sent_to_email,
        )

        self.session.add(
            challenge
        )

        await self.session.flush()

        await self.session.refresh(
            challenge
        )

        return challenge

    async def get_email_verification_challenge(
        self,
        challenge_id: uuid.UUID,
    ) -> EmailVerificationChallenge | None:
        result = await self.session.execute(
            select(
                EmailVerificationChallenge
            ).where(
                EmailVerificationChallenge.id
                == challenge_id
            )
        )

        return result.scalar_one_or_none()

    async def get_latest_email_verification_challenge(
        self,
        user_id: uuid.UUID,
    ) -> EmailVerificationChallenge | None:
        result = await self.session.execute(
            select(
                EmailVerificationChallenge
            )
            .where(
                EmailVerificationChallenge.user_id
                == user_id
            )
            .order_by(
                EmailVerificationChallenge.created_at.desc()
            )
            .limit(1)
        )

        return result.scalar_one_or_none()

    async def increment_email_verification_attempt(
        self,
        challenge: EmailVerificationChallenge,
    ) -> int:
        challenge.attempt_count += 1

        await self.session.flush()

        return challenge.attempt_count

    async def mark_email_verification_verified(
        self,
        challenge: EmailVerificationChallenge,
        *,
        verified_at: datetime,
    ) -> EmailVerificationChallenge:
        challenge.verified_at = verified_at
        challenge.consumed_at = verified_at

        await self.session.flush()

        return challenge

    async def invalidate_email_verification_challenge(
        self,
        challenge: EmailVerificationChallenge,
        *,
        invalidated_at: datetime,
    ) -> EmailVerificationChallenge:
        challenge.invalidated_at = invalidated_at

        await self.session.flush()

        return challenge

    async def invalidate_active_email_verification_challenges(
        self,
        *,
        user_id: uuid.UUID,
        invalidated_at: datetime,
    ) -> int:
        result = await self.session.execute(
            update(
                EmailVerificationChallenge
            )
            .where(
                EmailVerificationChallenge.user_id
                == user_id,
                EmailVerificationChallenge.consumed_at.is_(
                    None
                ),
                EmailVerificationChallenge.invalidated_at.is_(
                    None
                ),
            )
            .values(
                invalidated_at=invalidated_at
            )
        )

        return int(
            result.rowcount or 0
        )

    # =====================================================
    # PASSWORD RESET CHALLENGES
    # =====================================================

    async def create_password_reset_challenge(
        self,
        *,
        user_id: uuid.UUID,
        otp_hash: str,
        expires_at: datetime,
        max_attempts: int,
        requested_ip_address: str | None = None,
        requested_user_agent: str | None = None,
    ) -> PasswordResetChallenge:
        challenge = PasswordResetChallenge(
            user_id=user_id,
            otp_hash=otp_hash,
            expires_at=expires_at,
            max_attempts=max_attempts,
            requested_ip_address=requested_ip_address,
            requested_user_agent=requested_user_agent,
        )

        self.session.add(
            challenge
        )

        await self.session.flush()

        await self.session.refresh(
            challenge
        )

        return challenge

    async def get_password_reset_challenge(
        self,
        challenge_id: uuid.UUID,
    ) -> PasswordResetChallenge | None:
        result = await self.session.execute(
            select(
                PasswordResetChallenge
            ).where(
                PasswordResetChallenge.id
                == challenge_id
            )
        )

        return result.scalar_one_or_none()

    async def get_latest_password_reset_challenge(
        self,
        user_id: uuid.UUID,
    ) -> PasswordResetChallenge | None:
        result = await self.session.execute(
            select(
                PasswordResetChallenge
            )
            .where(
                PasswordResetChallenge.user_id
                == user_id
            )
            .order_by(
                PasswordResetChallenge.created_at.desc()
            )
            .limit(1)
        )

        return result.scalar_one_or_none()

    async def get_password_reset_by_reset_token_hash(
        self,
        reset_token_hash: str,
    ) -> PasswordResetChallenge | None:
        result = await self.session.execute(
            select(
                PasswordResetChallenge
            ).where(
                PasswordResetChallenge.reset_token_hash
                == reset_token_hash
            )
        )

        return result.scalar_one_or_none()

    async def increment_password_reset_attempt(
        self,
        challenge: PasswordResetChallenge,
    ) -> int:
        challenge.attempt_count += 1

        await self.session.flush()

        return challenge.attempt_count

    async def mark_password_reset_verified(
        self,
        challenge: PasswordResetChallenge,
        *,
        verified_at: datetime,
        reset_token_hash: str,
        reset_token_expires_at: datetime,
    ) -> PasswordResetChallenge:
        challenge.verified_at = verified_at
        challenge.reset_token_hash = (
            reset_token_hash
        )
        challenge.reset_token_expires_at = (
            reset_token_expires_at
        )

        await self.session.flush()

        return challenge

    async def consume_password_reset_challenge(
        self,
        challenge: PasswordResetChallenge,
        *,
        consumed_at: datetime,
    ) -> PasswordResetChallenge:
        challenge.consumed_at = consumed_at

        await self.session.flush()

        return challenge

    async def invalidate_password_reset_challenge(
        self,
        challenge: PasswordResetChallenge,
        *,
        invalidated_at: datetime,
    ) -> PasswordResetChallenge:
        challenge.invalidated_at = invalidated_at

        await self.session.flush()

        return challenge

    async def invalidate_active_password_reset_challenges(
        self,
        *,
        user_id: uuid.UUID,
        invalidated_at: datetime,
    ) -> int:
        result = await self.session.execute(
            update(
                PasswordResetChallenge
            )
            .where(
                PasswordResetChallenge.user_id
                == user_id,
                PasswordResetChallenge.consumed_at.is_(
                    None
                ),
                PasswordResetChallenge.invalidated_at.is_(
                    None
                ),
            )
            .values(
                invalidated_at=invalidated_at
            )
        )

        return int(
            result.rowcount or 0
        )


# =========================================================
# REPOSITORY FACTORY
# =========================================================


def get_auth_repository(
    session: AsyncSession,
) -> AuthRepository:
    return AuthRepository(
        session
    )


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "AuthRepository",
    "get_auth_repository",
]