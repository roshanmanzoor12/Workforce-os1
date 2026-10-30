from __future__ import annotations

from app.modules.auth.avatar_policy import sync_google_avatar

import asyncio
import re
import secrets
import smtplib
import ssl
import uuid
from datetime import (
    datetime,
    timezone,
)
from email.message import EmailMessage

from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.config import settings
from app.core.exceptions import (
    AccountDisabled,
    AccountLocked,
    ConflictError,
    EmailNotVerified,
    InvalidCredentials,
    InvalidToken,
    RateLimitExceeded,
    ResourceNotFound,
    ValidationError,
)
from app.core.logging import (
    get_logger,
)
from app.core.redis import (
    redis_increment,
)
from app.core.security import (
    normalize_email,
    normalize_username,
    verify_token_hash,
)
from app.modules.auth.email_verification import (
    issue_email_verification,
    resend_email_verification,
    verify_email_otp,
)
from app.modules.auth.events import (
    AuthEvent,
    all_sessions_revoked_event,
    email_verification_requested_event,
    email_verified_event,
    login_failed_event,
    login_succeeded_event,
    logout_all_succeeded_event,
    logout_succeeded_event,
    password_changed_event,
    password_reset_otp_verified_event,
    password_reset_requested_event,
    refresh_failed_event,
    refresh_succeeded_event,
    session_created_event,
    session_revoked_event,
    session_rotated_event,
    user_registered_event,
)
from app.modules.auth.google_oauth import (
    GoogleOAuthError,
    GoogleOAuthProviderError,
    GoogleOAuthProfileError,
    GoogleOAuthStateError,
    authenticate_google_authorization_code,
    build_google_authorization_url,
    create_google_oauth_state,
    verify_google_oauth_state,
)
from app.modules.auth.models import (
    RefreshSession,
    User,
)
from app.modules.auth.password_reset import (
    consume_password_reset,
    issue_password_reset,
    validate_password_reset_token,
    verify_password_reset_otp,
)
from app.modules.auth.passwords import (
    hash_password,
    validate_new_password,
    verify_password,
)
from app.modules.auth.repository import (
    AuthRepository,
)
from app.modules.billing.subscription_bootstrap import (
    SubscriptionBootstrapService,
)
from app.modules.auth.schemas import (
    CurrentUserResponse,
    EmailVerificationResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LogoutAllResponse,
    LogoutRequest,
    LogoutResponse,
    OAuthAuthorizationResponse,
    OAuthCallbackResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    ResendVerificationRequest,
    ResetPasswordRequest,
    ResetPasswordResponse,
    SessionPublic,
    SessionsResponse,
    SignupRequest,
    SignupResponse,
    TokenResponse,
    UserPublic,
    VerifyEmailRequest,
    VerifyResetOTPRequest,
    VerifyResetOTPResponse,
)
from app.modules.auth.tokens import (
    TokenPairData,
    create_refresh_token_hash,
    create_token_pair,
    is_expired,
    validate_refresh_token,
)


logger = get_logger(
    __name__
)


# =========================================================
# RATE LIMIT SETTINGS
# =========================================================

SIGNUP_RATE_LIMIT = 5
SIGNUP_RATE_WINDOW_SECONDS = (
    15 * 60
)

LOGIN_RATE_LIMIT = 10
LOGIN_RATE_WINDOW_SECONDS = (
    15 * 60
)

VERIFY_OTP_RATE_LIMIT = 10
VERIFY_OTP_WINDOW_SECONDS = (
    10 * 60
)

RESEND_VERIFICATION_RATE_LIMIT = 5
RESEND_VERIFICATION_WINDOW_SECONDS = (
    60 * 60
)

FORGOT_PASSWORD_RATE_LIMIT = 5
FORGOT_PASSWORD_WINDOW_SECONDS = (
    60 * 60
)

RESET_OTP_RATE_LIMIT = 10
RESET_OTP_WINDOW_SECONDS = (
    10 * 60
)

OAUTH_RATE_LIMIT = 20
OAUTH_RATE_WINDOW_SECONDS = (
    15 * 60
)


# =========================================================
# TIME
# =========================================================


def utc_now() -> datetime:
    return datetime.now(
        timezone.utc
    )


# =========================================================
# AUTH SERVICE
# =========================================================


from app.modules.auth.email_delivery import send_auth_email_sync

class AuthService:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session
        self.repository = (
            AuthRepository(
                session
            )
        )

    # =====================================================
    # SIGNUP
    # =====================================================
    async def signup(
        self,
        request: SignupRequest,
        *,
        ip_address: str | None = None,
        user_agent: str | None = None,
        request_id: str | None = None,
    ) -> SignupResponse:
        email = normalize_email(
            str(request.email)
        )

        username = (
            normalize_username(
                request.username
            )
        )

        await self._check_rate_limit(
            category="signup",
            identifier=(
                ip_address
                or email
            ),
            limit=SIGNUP_RATE_LIMIT,
            window_seconds=SIGNUP_RATE_WINDOW_SECONDS,
        )

        if await self.repository.email_exists(
            email
        ):
            raise ConflictError(
                "An account with this email already exists."
            )

        if await self.repository.username_exists(
            username
        ):
            raise ConflictError(
                "This username is already in use."
            )

        encoded_password = (
            hash_password(
                request.password
            )
        )

        try:
            user = (
                await self.repository
                .create_user(
                    email=email,
                    username=username,
                    password_hash=encoded_password,
                    first_name=request.first_name,
                    last_name=request.last_name,
                    is_email_verified=False,
                )
            )

            await SubscriptionBootstrapService(
                self.session
            ).ensure_for_user(
                user_id=user.id,
            )

            verification = (
                await issue_email_verification(
                    repository=self.repository,
                    user=user,
                )
            )

            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

        self._emit_event(
            user_registered_event(
                user_id=user.id,
                provider="local",
                ip_address=ip_address,
                user_agent=user_agent,
                request_id=request_id,
            )
        )

        self._emit_event(
            email_verification_requested_event(
                user_id=user.id,
                ip_address=ip_address,
                request_id=request_id,
            )
        )

        await self._send_verification_email(
            email=user.email,
            otp=verification.otp,
        )

        return SignupResponse(
            message=(
                "Account created. "
                "Please verify your email address."
            ),
            user=UserPublic.model_validate(
                user
            ),
            verification_required=True,
        )
    
    # =====================================================
    # EMAIL VERIFICATION
    # =====================================================

    async def verify_email(
        self,
        request: VerifyEmailRequest,
        *,
        ip_address: str | None = None,
        request_id: str | None = None,
    ) -> EmailVerificationResponse:
        email = normalize_email(
            str(request.email)
        )

        await self._check_rate_limit(
            category=
                "verify-email",
            identifier=
                ip_address
                or email,
            limit=
                VERIFY_OTP_RATE_LIMIT,
            window_seconds=
                VERIFY_OTP_WINDOW_SECONDS,
        )

        user = (
            await self.repository
            .get_user_by_email(
                email
            )
        )

        if user is None:
            raise ResourceNotFound(
                "User account was not found."
            )

        try:
            result = (
                await verify_email_otp(
                    repository=
                        self.repository,
                    user=
                        user,
                    otp=
                        request.otp,
                )
            )

            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

        self._emit_event(
            email_verified_event(
                user_id=
                    user.id,
                request_id=
                    request_id,
            )
        )

        return EmailVerificationResponse(
            message=
                "Email verified successfully.",
            verified=
                True,
            user=
                UserPublic
                .model_validate(
                    result.user
                ),
        )

    # =====================================================
    # RESEND VERIFICATION
    # =====================================================

    async def resend_verification(
        self,
        request: ResendVerificationRequest,
        *,
        ip_address: str | None = None,
        request_id: str | None = None,
    ) -> EmailVerificationResponse:
        email = normalize_email(
            str(request.email)
        )

        await self._check_rate_limit(
            category=
                "resend-verification",
            identifier=
                ip_address
                or email,
            limit=
                RESEND_VERIFICATION_RATE_LIMIT,
            window_seconds=
                RESEND_VERIFICATION_WINDOW_SECONDS,
        )

        user = (
            await self.repository
            .get_user_by_email(
                email
            )
        )

        if user is None:
            raise ResourceNotFound(
                "User account was not found."
            )

        try:
            result = (
                await resend_email_verification(
                    repository=
                        self.repository,
                    user=
                        user,
                )
            )

            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

        self._emit_event(
            email_verification_requested_event(
                user_id=
                    user.id,
                ip_address=
                    ip_address,
                request_id=
                    request_id,
            )
        )

        await self._send_verification_email(
            email=
                user.email,
            otp=
                result.otp,
        )

        return EmailVerificationResponse(
            message=(
                "A new verification code has been sent."
            ),
            verified=False,
            user=None,
        )

    # =====================================================
    # LOGIN
    # =====================================================

    async def login(
        self,
        request: LoginRequest,
        *,
        ip_address: str | None = None,
        user_agent: str | None = None,
        device_name: str | None = None,
        request_id: str | None = None,
    ) -> TokenResponse:
        identifier = (
            request.identifier
        )

        await self._check_rate_limit(
            category="login",
            identifier=
                ip_address
                or identifier,
            limit=
                LOGIN_RATE_LIMIT,
            window_seconds=
                LOGIN_RATE_WINDOW_SECONDS,
        )

        user = (
            await self.repository
            .get_user_by_identifier(
                identifier
            )
        )

        if user is None:
            self._emit_event(
                login_failed_event(
                    provider=
                        "local",
                    ip_address=
                        ip_address,
                    user_agent=
                        user_agent,
                    request_id=
                        request_id,
                    reason=
                        "user_not_found",
                )
            )

            raise InvalidCredentials(
                "Invalid email/username or password."
            )

        if not user.is_active:
            raise AccountDisabled(
                "This account is disabled."
            )

        if user.is_locked:
            raise AccountLocked(
                "This account is locked."
            )

        if not user.password_hash:
            self._emit_event(
                login_failed_event(
                    user_id=
                        user.id,
                    provider=
                        "local",
                    ip_address=
                        ip_address,
                    user_agent=
                        user_agent,
                    request_id=
                        request_id,
                    reason=
                        "local_password_not_configured",
                )
            )

            raise InvalidCredentials(
                "Local password login is not configured "
                "for this account."
            )

        if not verify_password(
            request.password,
            user.password_hash,
        ):
            try:
                await self.repository.increment_failed_login_attempts(
                    user
                )

                await self.session.commit()

            except Exception:
                await self.session.rollback()
                raise

            self._emit_event(
                login_failed_event(
                    user_id=
                        user.id,
                    provider=
                        "local",
                    ip_address=
                        ip_address,
                    user_agent=
                        user_agent,
                    request_id=
                        request_id,
                    reason=
                        "invalid_password",
                )
            )

            raise InvalidCredentials(
                "Invalid email/username or password."
            )

        if not user.is_email_verified:
            raise EmailNotVerified(
                "Please verify your email before signing in."
            )

        pair = create_token_pair(
            user_id=
                user.id
        )

        try:
            await self._persist_refresh_session(
                user=
                    user,
                pair=
                    pair,
                ip_address=
                    ip_address,
                user_agent=
                    user_agent,
                device_name=
                    device_name,
            )

            await self.repository.update_last_login(
                user,
                logged_in_at=
                    utc_now(),
            )

            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

        self._emit_event(
            session_created_event(
                user_id=
                    user.id,
                session_id=
                    pair.session_id,
                ip_address=
                    ip_address,
                user_agent=
                    user_agent,
                request_id=
                    request_id,
            )
        )

        self._emit_event(
            login_succeeded_event(
                user_id=
                    user.id,
                session_id=
                    pair.session_id,
                provider=
                    "local",
                ip_address=
                    ip_address,
                user_agent=
                    user_agent,
                request_id=
                    request_id,
            )
        )

        return TokenResponse(
            access_token=
                pair.access_token,
            refresh_token=
                pair.refresh_token,
            token_type=
                "bearer",
            expires_in=
                pair.expires_in,
            user=
                UserPublic
                .model_validate(
                    user
                ),
        )

    # =====================================================
    # GOOGLE OAUTH AUTHORIZATION
    # =====================================================

    async def google_authorization(
        self,
        *,
        client_id: str,
        redirect_uri: str,
        state_secret: str,
        intent: str,
        remember_me: bool = False,
        ip_address: str | None = None,
    ) -> OAuthAuthorizationResponse:
        await self._check_rate_limit(
            category=
                "google-oauth-start",
            identifier=
                ip_address
                or "anonymous",
            limit=
                OAUTH_RATE_LIMIT,
            window_seconds=
                OAUTH_RATE_WINDOW_SECONDS,
        )

        try:
            state = (
                create_google_oauth_state(
                    state_secret=
                        state_secret,
                    intent=
                        intent,
                    remember_me=
                        remember_me,
                )
            )

            authorization_url = (
                build_google_authorization_url(
                    client_id=
                        client_id,
                    redirect_uri=
                        redirect_uri,
                    state=
                        state.value,
                )
            )

        except GoogleOAuthError as exc:
            raise ValidationError(
                "Google authentication could not be started."
            ) from exc

        return OAuthAuthorizationResponse(
            provider=
                "google",
            authorization_url=
                authorization_url,
        )

    # =====================================================
    # GOOGLE OAUTH CALLBACK
    # =====================================================

    async def google_callback(
        self,
        *,
        code: str,
        state: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        state_secret: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
        device_name: str | None = None,
        request_id: str | None = None,
    ) -> OAuthCallbackResponse:
        await self._check_rate_limit(
            category=
                "google-oauth-callback",
            identifier=
                ip_address
                or "anonymous",
            limit=
                OAUTH_RATE_LIMIT,
            window_seconds=
                OAUTH_RATE_WINDOW_SECONDS,
        )

        try:
            state_payload = (
                verify_google_oauth_state(
                    state,
                    state_secret=
                        state_secret,
                )
            )

        except GoogleOAuthStateError as exc:
            raise InvalidToken(
                "OAuth state is invalid or expired."
            ) from exc

        intent = state_payload.get(
            "intent"
        )

        remember_me = (
            state_payload.get(
                "remember_me"
            )
        )

        if intent not in {
            "login",
            "signup",
        }:
            raise InvalidToken(
                "OAuth authentication intent is invalid."
            )

        if not isinstance(
            remember_me,
            bool,
        ):
            raise InvalidToken(
                "OAuth persistence preference is invalid."
            )

        try:
            profile, _provider_tokens = (
                await authenticate_google_authorization_code(
                    code=
                        code,
                    client_id=
                        client_id,
                    client_secret=
                        client_secret,
                    redirect_uri=
                        redirect_uri,
                )
            )

        except (
            GoogleOAuthProviderError,
            GoogleOAuthProfileError,
            GoogleOAuthError,
        ) as exc:
            raise InvalidCredentials(
                "Google authentication could not be completed."
            ) from exc

        if not profile.email_verified:
            raise EmailNotVerified(
                "Google account email is not verified."
            )

        email = normalize_email(
            profile.email
        )

        is_new_user = False

        try:
            identity = (
                await self.repository
                .get_auth_identity(
                    provider=
                        "google",
                    provider_user_id=
                        profile
                        .provider_user_id,
                )
            )
            if identity is not None:
                user = (
                    await self.repository
                    .get_user_by_id(
                        identity.user_id
                    )
                )

                if user is None:
                    raise InvalidCredentials(
                        "Google identity is not linked "
                        "to a valid account."
                    )

                await self.repository.update_auth_identity(
                    identity,
                    provider_email=
                        email,
                    provider_username=
                        None,
                    provider_avatar_url=
                        profile.avatar_url,
                )

            else:
                user = (
                    await self.repository
                    .get_user_by_email(
                        email
                    )
                )

                if user is None:
                    username = (
                        await self
                        ._allocate_oauth_username(
                            email=
                                email,
                        )
                    )

                    user = (
                        await self.repository
                        .create_user(
                            email=
                                email,
                            username=
                                username,
                            password_hash=
                                None,
                            first_name=
                                profile
                                .first_name,
                            last_name=
                                profile
                                .last_name,
                            is_email_verified=
                                True,
                        )
                    )

                    is_new_user = True

                    self._emit_event(
                        user_registered_event(
                            user_id=
                                user.id,
                            provider=
                                "google",
                            ip_address=
                                ip_address,
                            user_agent=
                                user_agent,
                            request_id=
                                request_id,
                        )
                    )

                else:
                    if (
                        not user
                        .is_email_verified
                    ):
                        await self.repository.mark_user_email_verified(
                            user,
                            verified_at=
                                utc_now(),
                        )

                await self.repository.create_auth_identity(
                    user_id=
                        user.id,
                    provider=
                        "google",
                    provider_user_id=
                        profile
                        .provider_user_id,
                    provider_email=
                        email,
                    provider_username=
                        None,
                    provider_avatar_url=
                        profile.avatar_url,
                )
                 
            sync_google_avatar(user, profile.avatar_url)

            if not user.is_active:
                raise AccountDisabled(
                    "This account is disabled."
                )

            if user.is_locked:
                raise AccountLocked(
                    "This account is locked."
                )

            pair = create_token_pair(
                user_id=
                    user.id
            )

            await self._persist_refresh_session(
                user=
                    user,
                pair=
                    pair,
                ip_address=
                    ip_address,
                user_agent=
                    user_agent,
                device_name=
                    device_name,
            )

            await self.repository.update_last_login(
                user,
                logged_in_at=
                    utc_now(),
            )

            await self.session.commit()

        except (
            AccountDisabled,
            AccountLocked,
            InvalidCredentials,
        ):
            await self.session.rollback()
            raise

        except Exception:
            await self.session.rollback()
            raise

        self._emit_event(
            session_created_event(
                user_id=
                    user.id,
                session_id=
                    pair.session_id,
                ip_address=
                    ip_address,
                user_agent=
                    user_agent,
                request_id=
                    request_id,
            )
        )

        self._emit_event(
            login_succeeded_event(
                user_id=
                    user.id,
                session_id=
                    pair.session_id,
                provider=
                    "google",
                ip_address=
                    ip_address,
                user_agent=
                    user_agent,
                request_id=
                    request_id,
            )
        )

        return OAuthCallbackResponse(
            access_token=
                pair.access_token,
            refresh_token=
                pair.refresh_token,
            token_type=
                "bearer",
            expires_in=
                pair.expires_in,
            user=
                UserPublic
                .model_validate(
                    user
                ),
            provider=
                "google",
            is_new_user=
                is_new_user,
            intent=
                intent,
            remember_me=
                remember_me,
        )

    # =====================================================
    # OAUTH USERNAME
    # =====================================================

    async def _allocate_oauth_username(
        self,
        *,
        email: str,
    ) -> str:
        local_part = (
            email.split(
                "@",
                1,
            )[0]
            .lower()
        )

        base = re.sub(
            r"[^a-z0-9._-]+",
            "",
            local_part,
        )

        base = base.strip(
            "._-"
        )

        if len(base) < 3:
            base = "user"

        base = base[:48]

        candidate = base

        if not await self.repository.username_exists(
            candidate
        ):
            return candidate

        for _ in range(20):
            suffix = (
                secrets.token_hex(
                    3
                )
            )

            candidate = (
                f"{base[:55]}"
                f"-{suffix}"
            )

            if not await self.repository.username_exists(
                candidate
            ):
                return candidate

        raise ConflictError(
            "Unable to allocate a unique username."
        )

    # =====================================================
    # REFRESH
    # =====================================================

    async def refresh(
        self,
        request: RefreshTokenRequest,
        *,
        ip_address: str | None = None,
        user_agent: str | None = None,
        request_id: str | None = None,
    ) -> RefreshTokenResponse:
        raw_token = (
            request.refresh_token
        )

        try:
            claims = (
                validate_refresh_token(
                    raw_token
                )
            )

            old_session = (
                await self.repository
                .get_refresh_session_by_id(
                    claims.session_id
                )
            )

            if old_session is None:
                raise InvalidToken(
                    "Refresh session was not found."
                )

            self._validate_refresh_session(
                session=
                    old_session,
                raw_token=
                    raw_token,
                claims_user_id=
                    claims.user_id,
                claims_jti=
                    claims.jti,
            )

            user = (
                await self.repository
                .get_user_by_id(
                    claims.user_id
                )
            )

            if user is None:
                raise InvalidToken(
                    "Authentication user was not found."
                )

            if not user.is_active:
                raise AccountDisabled(
                    "This account is disabled."
                )

            if user.is_locked:
                raise AccountLocked(
                    "This account is locked."
                )

            new_pair = (
                create_token_pair(
                    user_id=
                        user.id
                )
            )

            now = utc_now()

            await self.repository.mark_session_rotated(
                old_session,
                rotated_at=
                    now,
                replacement_session_id=
                    new_pair.session_id,
            )

            await self.repository.revoke_refresh_session(
                old_session,
                revoked_at=
                    now,
                reason=
                    "refresh_rotation",
            )

            await self._persist_refresh_session(
                user=
                    user,
                pair=
                    new_pair,
                ip_address=
                    ip_address,
                user_agent=
                    user_agent,
                device_name=
                    old_session
                    .device_name,
            )

            await self.session.commit()

        except Exception as exc:
            await self.session.rollback()

            self._emit_event(
                refresh_failed_event(
                    request_id=
                        request_id,
                    reason=
                        type(exc)
                        .__name__,
                )
            )

            raise

        self._emit_event(
            session_rotated_event(
                user_id=
                    user.id,
                session_id=
                    old_session.id,
                replacement_session_id=
                    new_pair.session_id,
                request_id=
                    request_id,
            )
        )

        self._emit_event(
            refresh_succeeded_event(
                user_id=
                    user.id,
                session_id=
                    new_pair.session_id,
                request_id=
                    request_id,
            )
        )

        return RefreshTokenResponse(
            access_token=
                new_pair.access_token,
            refresh_token=
                new_pair.refresh_token,
            token_type=
                "bearer",
            expires_in=
                new_pair.expires_in,
        )

    # =====================================================
    # LOGOUT
    # =====================================================

    async def logout(
        self,
        request: LogoutRequest,
        *,
        request_id: str | None = None,
    ) -> LogoutResponse:
        raw_token = (
            request.refresh_token
        )

        claims = (
            validate_refresh_token(
                raw_token
            )
        )

        session = (
            await self.repository
            .get_refresh_session_by_id(
                claims.session_id
            )
        )

        if session is None:
            return LogoutResponse(
                message=
                    "Session logged out.",
                success=
                    True,
            )

        if session.revoked_at is None:
            try:
                await self.repository.revoke_refresh_session(
                    session,
                    revoked_at=
                        utc_now(),
                    reason=
                        "logout",
                )

                await self.session.commit()

            except Exception:
                await self.session.rollback()
                raise

        self._emit_event(
            logout_succeeded_event(
                user_id=
                    claims.user_id,
                session_id=
                    claims.session_id,
                request_id=
                    request_id,
            )
        )

        return LogoutResponse(
            message=
                "Logged out successfully.",
            success=
                True,
        )

    # =====================================================
    # LOGOUT ALL
    # =====================================================

    async def logout_all(
        self,
        *,
        user: User,
        request_id: str | None = None,
    ) -> LogoutAllResponse:
        now = utc_now()

        try:
            revoked = (
                await self.repository
                .revoke_all_user_sessions(
                    user.id,
                    revoked_at=
                        now,
                    reason=
                        "logout_all",
                )
            )

            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

        self._emit_event(
            all_sessions_revoked_event(
                user_id=
                    user.id,
                revoked_sessions=
                    revoked,
                reason=
                    "logout_all",
                request_id=
                    request_id,
            )
        )

        self._emit_event(
            logout_all_succeeded_event(
                user_id=
                    user.id,
                revoked_sessions=
                    revoked,
                request_id=
                    request_id,
            )
        )

        return LogoutAllResponse(
            message=
                "All sessions have been logged out.",
            revoked_sessions=
                revoked,
        )

    # =====================================================
    # FORGOT PASSWORD
    # =====================================================

    async def forgot_password(
        self,
        request: ForgotPasswordRequest,
        *,
        ip_address: str | None = None,
        user_agent: str | None = None,
        request_id: str | None = None,
    ) -> ForgotPasswordResponse:
        email = normalize_email(
            str(request.email)
        )

        await self._check_rate_limit(
            category=
                "forgot-password",
            identifier=
                ip_address
                or email,
            limit=
                FORGOT_PASSWORD_RATE_LIMIT,
            window_seconds=
                FORGOT_PASSWORD_WINDOW_SECONDS,
        )

        generic_response = (
            ForgotPasswordResponse(
                message=(
                    "If an account exists for that email, "
                    "password reset instructions have been sent."
                ),
                success=True,
            )
        )

        user = (
            await self.repository
            .get_user_by_email(
                email
            )
        )

        if user is None:
            self._emit_event(
                password_reset_requested_event(
                    user_id=None,
                    ip_address=
                        ip_address,
                    user_agent=
                        user_agent,
                    request_id=
                        request_id,
                )
            )

            return generic_response

        try:
            reset = (
                await issue_password_reset(
                    repository=
                        self.repository,
                    user=
                        user,
                    requested_ip_address=
                        ip_address,
                    requested_user_agent=
                        user_agent,
                )
            )

            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

        self._emit_event(
            password_reset_requested_event(
                user_id=
                    user.id,
                ip_address=
                    ip_address,
                user_agent=
                    user_agent,
                request_id=
                    request_id,
            )
        )

        await self._send_password_reset_email(
            email=
                user.email,
            otp=
                reset.otp,
        )

        return generic_response

    # =====================================================
    # VERIFY RESET OTP
    # =====================================================

    async def verify_reset_otp(
        self,
        request: VerifyResetOTPRequest,
        *,
        ip_address: str | None = None,
        request_id: str | None = None,
    ) -> VerifyResetOTPResponse:
        email = normalize_email(
            str(request.email)
        )

        await self._check_rate_limit(
            category=
                "verify-reset-otp",
            identifier=
                ip_address
                or email,
            limit=
                RESET_OTP_RATE_LIMIT,
            window_seconds=
                RESET_OTP_WINDOW_SECONDS,
        )

        user = (
            await self.repository
            .get_user_by_email(
                email
            )
        )

        if user is None:
            raise ValidationError(
                "Password reset code is invalid or expired."
            )

        try:
            result = (
                await verify_password_reset_otp(
                    repository=
                        self.repository,
                    user=
                        user,
                    otp=
                        request.otp,
                )
            )

            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

        self._emit_event(
            password_reset_otp_verified_event(
                user_id=
                    user.id,
                request_id=
                    request_id,
            )
        )

        remaining_seconds = int(
            (
                result
                .reset_token_expires_at
                - utc_now()
            ).total_seconds()
        )

        return VerifyResetOTPResponse(
            message=
                "Password reset code verified.",
            verified=
                True,
            reset_token=
                result.reset_token,
            reset_token_expires_in=
                max(
                    1,
                    remaining_seconds,
                ),
        )

    # =====================================================
    # RESET PASSWORD
    # =====================================================

    async def reset_password(
        self,
        request: ResetPasswordRequest,
        *,
        request_id: str | None = None,
    ) -> ResetPasswordResponse:
        authorization = (
            await validate_password_reset_token(
                repository=
                    self.repository,
                reset_token=
                    request.reset_token,
            )
        )

        try:
            user_id = uuid.UUID(
                str(
                    authorization
                    .user_id
                )
            )

        except ValueError as exc:
            raise ValidationError(
                "Password reset authorization is invalid."
            ) from exc

        user = (
            await self.repository
            .get_user_by_id(
                user_id
            )
        )

        if user is None:
            raise ResourceNotFound(
                "User account was not found."
            )

        validate_new_password(
            new_password=
                request.new_password,
            confirm_password=
                request.confirm_password,
        )

        encoded_password = (
            hash_password(
                request.new_password
            )
        )

        now = utc_now()

        try:
            await self.repository.update_user_password(
                user,
                password_hash=
                    encoded_password,
                changed_at=
                    now,
            )

            await consume_password_reset(
                repository=
                    self.repository,
                challenge=
                    authorization
                    .challenge,
            )

            await self.repository.invalidate_active_password_reset_challenges(
                user_id=
                    user.id,
                invalidated_at=
                    now,
            )

            revoked = (
                await self.repository
                .revoke_all_user_sessions(
                    user.id,
                    revoked_at=
                        now,
                    reason=
                        "password_reset",
                )
            )

            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

        self._emit_event(
            password_changed_event(
                user_id=
                    user.id,
                request_id=
                    request_id,
            )
        )

        self._emit_event(
            all_sessions_revoked_event(
                user_id=
                    user.id,
                revoked_sessions=
                    revoked,
                reason=
                    "password_reset",
                request_id=
                    request_id,
            )
        )

        return ResetPasswordResponse(
            message=(
                "Password has been reset successfully. "
                "Please sign in again."
            ),
            success=True,
        )

    # =====================================================
    # CURRENT USER
    # =====================================================

    async def current_user(
        self,
        user: User,
    ) -> CurrentUserResponse:
        return CurrentUserResponse(
            user=
                UserPublic
                .model_validate(
                    user
                )
        )

    # =====================================================
    # SESSION LIST
    # =====================================================

    async def list_sessions(
        self,
        *,
        user: User,
    ) -> SessionsResponse:
        sessions = (
            await self.repository
            .list_user_refresh_sessions(
                user.id,
                include_revoked=
                    False,
            )
        )

        public_sessions = [
            SessionPublic.model_validate(
                session
            )
            for session in sessions
        ]

        return SessionsResponse(
            sessions=
                public_sessions,
            total=
                len(
                    public_sessions
                ),
        )

    # =====================================================
    # REVOKE ONE SESSION
    # =====================================================

    async def revoke_session(
        self,
        *,
        user: User,
        session_id: uuid.UUID,
        request_id: str | None = None,
    ) -> LogoutResponse:
        session = (
            await self.repository
            .get_refresh_session_by_id(
                session_id
            )
        )

        if (
            session is None
            or session.user_id !=
                user.id
        ):
            raise ResourceNotFound(
                "Session was not found."
            )

        try:
            await self.repository.revoke_refresh_session(
                session,
                revoked_at=
                    utc_now(),
                reason=
                    "user_session_revocation",
            )

            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

        self._emit_event(
            session_revoked_event(
                user_id=
                    user.id,
                session_id=
                    session.id,
                reason=
                    "user_session_revocation",
                request_id=
                    request_id,
            )
        )

        return LogoutResponse(
            message=
                "Session revoked successfully.",
            success=
                True,
        )

    # =====================================================
    # REFRESH SESSION PERSISTENCE
    # =====================================================

    async def _persist_refresh_session(
        self,
        *,
        user: User,
        pair: TokenPairData,
        ip_address: str | None,
        user_agent: str | None,
        device_name: str | None,
    ) -> RefreshSession:
        token_digest = (
            create_refresh_token_hash(
                pair.refresh_token
            )
        )

        return (
            await self.repository
            .create_refresh_session(
                session_id=
                    pair.session_id,
                user_id=
                    user.id,
                jti=
                    pair.refresh_jti,
                token_hash=
                    token_digest,
                expires_at=
                    pair.refresh_expires_at,
                device_name=
                    device_name,
                user_agent=
                    user_agent,
                ip_address=
                    ip_address,
            )
        )

    # =====================================================
    # REFRESH SESSION VALIDATION
    # =====================================================

    def _validate_refresh_session(
        self,
        *,
        session: RefreshSession,
        raw_token: str,
        claims_user_id: uuid.UUID,
        claims_jti: str,
    ) -> None:
        if (
            session.user_id !=
            claims_user_id
        ):
            raise InvalidToken(
                "Refresh session user does not match."
            )

        if (
            session.jti !=
            claims_jti
        ):
            raise InvalidToken(
                "Refresh session identifier does not match."
            )

        if (
            session.revoked_at
            is not None
        ):
            raise InvalidToken(
                "Refresh session has been revoked."
            )

        if (
            session.rotated_at
            is not None
        ):
            raise InvalidToken(
                "Refresh token has already been rotated."
            )

        if is_expired(
            session.expires_at
        ):
            raise InvalidToken(
                "Refresh session has expired."
            )

        if not verify_token_hash(
            raw_token,
            session.token_hash,
        ):
            raise InvalidToken(
                "Refresh token does not match "
                "the stored session."
            )

    # =====================================================
    # RATE LIMITING
    # =====================================================

    async def _check_rate_limit(
        self,
        *,
        category: str,
        identifier: str,
        limit: int,
        window_seconds: int,
    ) -> None:
        safe_identifier = (
            identifier
            .strip()
            .lower()
            if identifier
            else "unknown"
        )

        key = (
            f"auth:rate:"
            f"{category}:"
            f"{safe_identifier}"
        )

        count = (
            await redis_increment(
                key,
                amount=1,
                expire_seconds=
                    window_seconds,
            )
        )

        if count > limit:
            raise RateLimitExceeded(
                "Too many authentication attempts. "
                "Please try again later."
            )

    # =====================================================
    # AUTH EVENTS
    # =====================================================

    def _emit_event(
        self,
        event: AuthEvent,
    ) -> None:
        payload = (
            event.to_dict()
        )

        if (
            event.severity ==
            "critical"
        ):
            logger.error(
                "auth_domain_event",
                auth_event=
                    payload,
            )

        elif (
            event.severity ==
            "warning"
        ):
            logger.warning(
                "auth_domain_event",
                auth_event=
                    payload,
            )

        else:
            logger.info(
                "auth_domain_event",
                auth_event=
                    payload,
            )

    # =====================================================
    # EMAIL
    # =====================================================

    async def _send_verification_email(
        self,
        *,
        email: str,
        otp: str,
    ) -> None:
        await self._send_email(
            recipient=email,
            subject=f"Verify your {settings.app_name} email",
            text=(
                f"Your {settings.app_name} verification code is: "
                f"{otp}\n\n"
                f"This code expires in "
                f"{settings.email_verification_otp_minutes} minutes.\n\n"
                "If you did not create this account, "
                "you can ignore this email."
            ),
        )

    async def _send_password_reset_email(
        self,
        *,
        email: str,
        otp: str,
    ) -> None:
        await self._send_email(
            recipient=email,
            subject=f"Reset your {settings.app_name} password",
            text=(
                f"Your {settings.app_name} password reset code is: "
                f"{otp}\n\n"
                f"This code expires in "
                f"{settings.password_reset_otp_minutes} minutes.\n\n"
                "If you did not request a password reset, "
                "you can ignore this email."
            ),
        )

    async def _send_email(
        self,
        *,
        recipient: str,
        subject: str,
        text: str,
    ) -> None:
        await asyncio.to_thread(
            self._send_email_sync,
            recipient,
            subject,
            text,
        )

    def _send_email_sync(
        self,
        recipient: str,
        subject: str,
        text: str,
    ) -> None:
        send_auth_email_sync(
            recipient,
            subject,
            text,
        )


# =========================================================
# FACTORY
# =========================================================


def get_auth_service(
    session: AsyncSession,
) -> AuthService:
    return AuthService(
        session
    )


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "AuthService",
    "get_auth_service",
]



