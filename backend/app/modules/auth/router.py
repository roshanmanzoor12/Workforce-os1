from __future__ import annotations
from fastapi import HTTPException
from app.modules.auth.schemas import OAuthCallbackResponse

import os
import uuid
from typing import Annotated
from urllib.parse import urlencode

from fastapi import (
    APIRouter,
    Depends,
    Query,
    Request,
    status,
)
from fastapi.responses import (
    RedirectResponse,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.config import settings
from app.core.database import (
    get_control_db,
)
from app.core.exceptions import (
    AccountDisabled,
    AccountLocked,
    EmailNotVerified,
    InvalidCredentials,
    InvalidToken,
    ValidationError,
)
from app.middleware.request_id import (
    get_request_id,
)
from app.modules.auth.models import (
    User,
)
from app.modules.auth.oauth_handoff import (
    consume_oauth_handoff,
    create_oauth_handoff,
)
from app.modules.auth.permissions import (
    get_current_user,
    get_current_verified_user,
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
    OAuthExchangeRequest,
    OAuthExchangeResponse,
    OAuthIntent,
    RefreshTokenRequest,
    RefreshTokenResponse,
    ResendVerificationRequest,
    ResetPasswordRequest,
    ResetPasswordResponse,
    SessionsResponse,
    SignupRequest,
    SignupResponse,
    TokenResponse,
    VerifyEmailRequest,
    VerifyResetOTPRequest,
    VerifyResetOTPResponse,
)
from app.modules.auth.service import (
    AuthService,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


# =========================================================
# DEPENDENCIES
# =========================================================


ControlDB = Annotated[
    AsyncSession,
    Depends(get_control_db),
]


CurrentUser = Annotated[
    User,
    Depends(get_current_user),
]


VerifiedUser = Annotated[
    User,
    Depends(
        get_current_verified_user
    ),
]


def get_auth_service(
    db: ControlDB,
) -> AuthService:
    return AuthService(
        db
    )


AuthServiceDependency = Annotated[
    AuthService,
    Depends(get_auth_service),
]


# =========================================================
# HELPERS
# =========================================================


def get_client_ip(
    request: Request,
) -> str | None:
    if request.client is None:
        return None

    return request.client.host


def get_user_agent(
    request: Request,
) -> str | None:
    value = request.headers.get(
        "user-agent"
    )

    if not value:
        return None

    return value[:2000]


def get_device_name(
    request: Request,
) -> str | None:
    value = request.headers.get(
        "x-device-name"
    )

    if not value:
        return None

    return value.strip()[:255]


def get_google_state_secret() -> str:
    return (
        "workforceos:google-oauth-state:"
        f"{settings.google_client_secret}"
    )


def get_frontend_base_url() -> str:
    return (
        os.getenv(
            "WORKFORCE_WEB_URL",
            "http://localhost:3001",
        )
        .strip()
        .rstrip("/")
    )


# =========================================================
# SIGNUP
# =========================================================


@router.post(
    "/signup",
    response_model=SignupResponse,
    status_code=
        status.HTTP_201_CREATED,
    summary=
        "Create a WorkforceOS account",
)
async def signup(
    payload: SignupRequest,
    request: Request,
    auth: AuthServiceDependency,
) -> SignupResponse:
    return await auth.signup(
        payload,
        ip_address=
            get_client_ip(
                request
            ),
        user_agent=
            get_user_agent(
                request
            ),
        request_id=
            get_request_id(
                request
            ),
    )


# =========================================================
# VERIFY EMAIL
# =========================================================


@router.post(
    "/verify-email",
    response_model=
        EmailVerificationResponse,
    status_code=
        status.HTTP_200_OK,
)
async def verify_email(
    payload: VerifyEmailRequest,
    request: Request,
    auth: AuthServiceDependency,
) -> EmailVerificationResponse:
    return await auth.verify_email(
        payload,
        ip_address=
            get_client_ip(
                request
            ),
        request_id=
            get_request_id(
                request
            ),
    )


@router.post(
    "/resend-verification",
    response_model=
        EmailVerificationResponse,
    status_code=
        status.HTTP_200_OK,
)
async def resend_verification(
    payload:
        ResendVerificationRequest,
    request: Request,
    auth: AuthServiceDependency,
) -> EmailVerificationResponse:
    return await auth.resend_verification(
        payload,
        ip_address=
            get_client_ip(
                request
            ),
        request_id=
            get_request_id(
                request
            ),
    )


# =========================================================
# LOGIN
# =========================================================


@router.post(
    "/login",
    response_model=
        TokenResponse,
    status_code=
        status.HTTP_200_OK,
)
async def login(
    payload: LoginRequest,
    request: Request,
    auth: AuthServiceDependency,
) -> TokenResponse:
    return await auth.login(
        payload,
        ip_address=
            get_client_ip(
                request
            ),
        user_agent=
            get_user_agent(
                request
            ),
        device_name=
            get_device_name(
                request
            ),
        request_id=
            get_request_id(
                request
            ),
    )


# =========================================================
# GOOGLE AUTHORIZE
# =========================================================


@router.get(
    "/oauth/google/authorize",
    response_model=
        OAuthAuthorizationResponse,
    status_code=
        status.HTTP_200_OK,
    summary=
        "Start Google authentication",
)
async def google_oauth_authorize(
    request: Request,
    auth: AuthServiceDependency,
    intent: Annotated[
        OAuthIntent,
        Query(),
    ] = "login",
    remember_me: Annotated[
        bool,
        Query(),
    ] = False,
) -> OAuthAuthorizationResponse:
    return await auth.google_authorization(
        client_id=
            settings.google_client_id,
        redirect_uri=
            settings.google_redirect_uri,
        state_secret=
            get_google_state_secret(),
        intent=
            intent,
        remember_me=
            remember_me,
        ip_address=
            get_client_ip(
                request
            ),
    )


# =========================================================
# GOOGLE CALLBACK
# =========================================================


@router.get(
    "/oauth/google/callback",
    response_class=RedirectResponse,
    status_code=status.HTTP_303_SEE_OTHER,
    summary="Complete Google authentication",
)
async def google_oauth_callback(
    request: Request,
    auth: AuthServiceDependency,
    code: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=4096,
        ),
    ] = None,
    state: Annotated[
        str | None,
        Query(
            min_length=20,
            max_length=8192,
        ),
    ] = None,
    error: Annotated[
        str | None,
        Query(max_length=512),
    ] = None,
) -> RedirectResponse:
    frontend_callback = (
        f"{get_frontend_base_url()}/oauth/callback"
    )

    def redirect_to_frontend(
        parameters: dict[str, str],
    ) -> RedirectResponse:
        response = RedirectResponse(
            url=(
                f"{frontend_callback}?"
                f"{urlencode(parameters)}"
            ),
            status_code=status.HTTP_303_SEE_OTHER,
        )
        response.headers["Cache-Control"] = "no-store"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response

    if error:
        return redirect_to_frontend(
            {
                "error": (
                    "access_denied"
                    if error == "access_denied"
                    else "google_authentication_failed"
                ),
            }
        )

    if not code or not state:
        return redirect_to_frontend(
            {
                "error": "invalid_oauth_callback",
            }
        )

    try:
        result = await auth.google_callback(
            code=code,
            state=state,
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
            redirect_uri=settings.google_redirect_uri,
            state_secret=get_google_state_secret(),
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            device_name=get_device_name(request),
            request_id=get_request_id(request),
        )
    except (
        InvalidCredentials,
        InvalidToken,
        EmailNotVerified,
        AccountDisabled,
        AccountLocked,
        ValidationError,
    ):
        return redirect_to_frontend(
            {
                "error": "google_authentication_failed",
            }
        )

    handoff_code = await create_oauth_handoff(
        result
    )

    return redirect_to_frontend(
        {
            "code": handoff_code,
        }
    )

# =========================================================
# OAUTH EXCHANGE
# =========================================================


@router.post(
    "/oauth/exchange",
    response_model=
        OAuthExchangeResponse,
    status_code=
        status.HTTP_200_OK,
)
async def oauth_exchange(
    payload:
        OAuthExchangeRequest,
) -> OAuthExchangeResponse:
    result = (
        await consume_oauth_handoff(
            payload.code
        )
    )

    return OAuthExchangeResponse(
        **result.model_dump()
    )


# =========================================================
# REFRESH
# =========================================================


@router.post(
    "/refresh",
    response_model=
        RefreshTokenResponse,
    status_code=
        status.HTTP_200_OK,
)
async def refresh(
    payload:
        RefreshTokenRequest,
    request: Request,
    auth: AuthServiceDependency,
) -> RefreshTokenResponse:
    return await auth.refresh(
        payload,
        ip_address=
            get_client_ip(
                request
            ),
        user_agent=
            get_user_agent(
                request
            ),
        request_id=
            get_request_id(
                request
            ),
    )


# =========================================================
# LOGOUT
# =========================================================


@router.post(
    "/logout",
    response_model=
        LogoutResponse,
    status_code=
        status.HTTP_200_OK,
)
async def logout(
    payload: LogoutRequest,
    request: Request,
    auth: AuthServiceDependency,
) -> LogoutResponse:
    return await auth.logout(
        payload,
        request_id=
            get_request_id(
                request
            ),
    )


@router.post(
    "/logout-all",
    response_model=
        LogoutAllResponse,
    status_code=
        status.HTTP_200_OK,
)
async def logout_all(
    request: Request,
    auth: AuthServiceDependency,
    current_user: CurrentUser,
) -> LogoutAllResponse:
    return await auth.logout_all(
        user=
            current_user,
        request_id=
            get_request_id(
                request
            ),
    )


# =========================================================
# FORGOT PASSWORD
# =========================================================


@router.post(
    "/forgot-password",
    response_model=
        ForgotPasswordResponse,
    status_code=
        status.HTTP_200_OK,
)
async def forgot_password(
    payload:
        ForgotPasswordRequest,
    request: Request,
    auth: AuthServiceDependency,
) -> ForgotPasswordResponse:
    return await auth.forgot_password(
        payload,
        ip_address=
            get_client_ip(
                request
            ),
        user_agent=
            get_user_agent(
                request
            ),
        request_id=
            get_request_id(
                request
            ),
    )


# =========================================================
# VERIFY RESET OTP
# =========================================================


@router.post(
    "/verify-reset-otp",
    response_model=
        VerifyResetOTPResponse,
    status_code=
        status.HTTP_200_OK,
)
async def verify_reset_otp(
    payload:
        VerifyResetOTPRequest,
    request: Request,
    auth: AuthServiceDependency,
) -> VerifyResetOTPResponse:
    return await auth.verify_reset_otp(
        payload,
        ip_address=
            get_client_ip(
                request
            ),
        request_id=
            get_request_id(
                request
            ),
    )


# =========================================================
# RESET PASSWORD
# =========================================================


@router.post(
    "/reset-password",
    response_model=
        ResetPasswordResponse,
    status_code=
        status.HTTP_200_OK,
)
async def reset_password(
    payload:
        ResetPasswordRequest,
    request: Request,
    auth: AuthServiceDependency,
) -> ResetPasswordResponse:
    return await auth.reset_password(
        payload,
        request_id=
            get_request_id(
                request
            ),
    )


# =========================================================
# CURRENT USER
# =========================================================


@router.get(
    "/me",
    response_model=
        CurrentUserResponse,
    status_code=
        status.HTTP_200_OK,
)
async def me(
    auth: AuthServiceDependency,
    current_user: CurrentUser,
) -> CurrentUserResponse:
    return await auth.current_user(
        current_user
    )


@router.get(
    "/me/verified",
    response_model=
        CurrentUserResponse,
    status_code=
        status.HTTP_200_OK,
)
async def me_verified(
    auth: AuthServiceDependency,
    current_user: VerifiedUser,
) -> CurrentUserResponse:
    return await auth.current_user(
        current_user
    )


# =========================================================
# SESSIONS
# =========================================================


@router.get(
    "/sessions",
    response_model=
        SessionsResponse,
    status_code=
        status.HTTP_200_OK,
)
async def list_sessions(
    auth: AuthServiceDependency,
    current_user: CurrentUser,
) -> SessionsResponse:
    return await auth.list_sessions(
        user=
            current_user
    )


@router.delete(
    "/sessions/{session_id}",
    response_model=
        LogoutResponse,
    status_code=
        status.HTTP_200_OK,
)
async def revoke_session(
    session_id: uuid.UUID,
    request: Request,
    auth: AuthServiceDependency,
    current_user: CurrentUser,
) -> LogoutResponse:
    return await auth.revoke_session(
        user=
            current_user,
        session_id=
            session_id,
        request_id=
            get_request_id(
                request
            ),
    )


__all__ = [
    "router",
]
