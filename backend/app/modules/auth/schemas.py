from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

from app.config import settings
from app.core.security import (
    normalize_email,
    normalize_username,
)


# =========================================================
# SHARED TYPES
# =========================================================

AuthProvider = Literal[
    "local",
    "google",
    "github",
]

ExternalAuthProvider = Literal[
    "google",
    "github",
]

TokenType = Literal[
    "bearer",
]

OAuthIntent = Literal[
    "login",
    "signup",
]


# =========================================================
# COMMON BASE SCHEMA
# =========================================================

class AuthSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        extra="forbid",
    )


# =========================================================
# USER OUTPUT
# =========================================================

class UserPublic(AuthSchema):
    id: uuid.UUID
    email: EmailStr
    username: str

    first_name: str | None = None
    last_name: str | None = None
    avatar_url: str | None = None
    avatar_source: str = "auto"

    is_email_verified: bool
    is_active: bool
    is_locked: bool

    created_at: datetime
    updated_at: datetime


# =========================================================
# SIGNUP
# =========================================================

class SignupRequest(AuthSchema):
    email: EmailStr

    username: str = Field(
        min_length=3,
        max_length=64,
    )

    password: str = Field(
        min_length=
            settings.password_min_length,
        max_length=128,
    )

    confirm_password: str = Field(
        min_length=
            settings.password_min_length,
        max_length=128,
    )

    first_name: str | None = Field(
        default=None,
        max_length=100,
    )

    last_name: str | None = Field(
        default=None,
        max_length=100,
    )

    @field_validator(
        "email"
    )
    @classmethod
    def normalize_signup_email(
        cls,
        value: EmailStr,
    ) -> str:
        return normalize_email(
            str(value)
        )

    @field_validator(
        "username"
    )
    @classmethod
    def validate_username(
        cls,
        value: str,
    ) -> str:
        normalized = (
            normalize_username(
                value
            )
        )

        if len(normalized) < 3:
            raise ValueError(
                "Username must contain at least 3 characters."
            )

        if len(normalized) > 64:
            raise ValueError(
                "Username must contain at most 64 characters."
            )

        if not re.fullmatch(
            r"[a-z0-9._-]+",
            normalized,
        ):
            raise ValueError(
                "Username may contain only lowercase letters, "
                "numbers, dots, underscores, and hyphens."
            )

        if normalized.startswith(
            (
                ".",
                "-",
                "_",
            )
        ):
            raise ValueError(
                "Username cannot start with punctuation."
            )

        if normalized.endswith(
            (
                ".",
                "-",
                "_",
            )
        ):
            raise ValueError(
                "Username cannot end with punctuation."
            )

        return normalized

    @field_validator(
        "password"
    )
    @classmethod
    def validate_password_policy(
        cls,
        value: str,
    ) -> str:
        if (
            len(value) <
            settings.password_min_length
        ):
            raise ValueError(
                f"Password must contain at least "
                f"{settings.password_min_length} characters."
            )

        if (
            settings
            .password_require_letter
        ):
            if not re.search(
                r"[A-Za-z]",
                value,
            ):
                raise ValueError(
                    "Password must contain at least one letter."
                )

        if (
            settings
            .password_require_number
        ):
            if not re.search(
                r"\d",
                value,
            ):
                raise ValueError(
                    "Password must contain at least one number."
                )

        if (
            settings
            .password_require_special
        ):
            if not re.search(
                r"[^A-Za-z0-9]",
                value,
            ):
                raise ValueError(
                    "Password must contain at least one special character."
                )

        return value

    @model_validator(
        mode="after"
    )
    def passwords_match(
        self,
    ) -> "SignupRequest":
        if (
            self.password !=
            self.confirm_password
        ):
            raise ValueError(
                "Password and confirm password do not match."
            )

        return self


class SignupResponse(AuthSchema):
    message: str
    user: UserPublic
    verification_required: bool = True


# =========================================================
# EMAIL VERIFICATION
# =========================================================

class VerifyEmailRequest(AuthSchema):
    email: EmailStr

    otp: str = Field(
        min_length=4,
        max_length=10,
    )

    @field_validator(
        "email"
    )
    @classmethod
    def normalize_verify_email(
        cls,
        value: EmailStr,
    ) -> str:
        return normalize_email(
            str(value)
        )

    @field_validator(
        "otp"
    )
    @classmethod
    def validate_otp(
        cls,
        value: str,
    ) -> str:
        otp = value.strip()

        if not otp.isdigit():
            raise ValueError(
                "OTP must contain digits only."
            )

        if (
            len(otp) !=
            settings.otp_length
        ):
            raise ValueError(
                f"OTP must contain exactly "
                f"{settings.otp_length} digits."
            )

        return otp


class ResendVerificationRequest(
    AuthSchema
):
    email: EmailStr

    @field_validator(
        "email"
    )
    @classmethod
    def normalize_resend_email(
        cls,
        value: EmailStr,
    ) -> str:
        return normalize_email(
            str(value)
        )


class EmailVerificationResponse(
    AuthSchema
):
    message: str
    verified: bool
    user: UserPublic | None = None


# =========================================================
# LOGIN
# =========================================================

class LoginRequest(AuthSchema):
    identifier: str = Field(
        min_length=3,
        max_length=320,
    )

    password: str = Field(
        min_length=1,
        max_length=128,
    )

    remember_me: bool = False

    @field_validator(
        "identifier"
    )
    @classmethod
    def normalize_identifier(
        cls,
        value: str,
    ) -> str:
        raw = value.strip()

        if "@" in raw:
            return normalize_email(
                raw
            )

        return normalize_username(
            raw
        )


# =========================================================
# TOKENS
# =========================================================

class TokenResponse(AuthSchema):
    access_token: str
    refresh_token: str

    token_type: TokenType = (
        "bearer"
    )

    expires_in: int = Field(
        gt=0,
    )

    user: UserPublic


class RefreshTokenRequest(
    AuthSchema
):
    refresh_token: str = Field(
        min_length=20,
    )


class RefreshTokenResponse(
    AuthSchema
):
    access_token: str
    refresh_token: str

    token_type: TokenType = (
        "bearer"
    )

    expires_in: int = Field(
        gt=0,
    )


# =========================================================
# LOGOUT
# =========================================================

class LogoutRequest(AuthSchema):
    refresh_token: str = Field(
        min_length=20,
    )


class LogoutResponse(AuthSchema):
    message: str
    success: bool = True


class LogoutAllResponse(AuthSchema):
    message: str

    revoked_sessions: int = Field(
        ge=0,
    )


# =========================================================
# FORGOT PASSWORD
# =========================================================

class ForgotPasswordRequest(
    AuthSchema
):
    email: EmailStr

    @field_validator(
        "email"
    )
    @classmethod
    def normalize_forgot_email(
        cls,
        value: EmailStr,
    ) -> str:
        return normalize_email(
            str(value)
        )


class ForgotPasswordResponse(
    AuthSchema
):
    message: str
    success: bool = True


# =========================================================
# VERIFY RESET OTP
# =========================================================

class VerifyResetOTPRequest(
    AuthSchema
):
    email: EmailStr

    otp: str = Field(
        min_length=4,
        max_length=10,
    )

    @field_validator(
        "email"
    )
    @classmethod
    def normalize_reset_email(
        cls,
        value: EmailStr,
    ) -> str:
        return normalize_email(
            str(value)
        )

    @field_validator(
        "otp"
    )
    @classmethod
    def validate_reset_otp(
        cls,
        value: str,
    ) -> str:
        otp = value.strip()

        if not otp.isdigit():
            raise ValueError(
                "OTP must contain digits only."
            )

        if (
            len(otp) !=
            settings.otp_length
        ):
            raise ValueError(
                f"OTP must contain exactly "
                f"{settings.otp_length} digits."
            )

        return otp


class VerifyResetOTPResponse(
    AuthSchema
):
    message: str
    verified: bool
    reset_token: str | None = None

    reset_token_expires_in:int | None = Field(
            default=None,
            gt=0,
        )


# =========================================================
# RESET PASSWORD
# =========================================================

class ResetPasswordRequest(
    AuthSchema
):
    reset_token: str = Field(
        min_length=20,
    )

    new_password: str = Field(
        min_length=
            settings.password_min_length,
        max_length=128,
    )

    confirm_password: str = Field(
        min_length=
            settings.password_min_length,
        max_length=128,
    )

    @field_validator(
        "new_password"
    )
    @classmethod
    def validate_new_password(
        cls,
        value: str,
    ) -> str:
        if (
            len(value) <
            settings.password_min_length
        ):
            raise ValueError(
                f"Password must contain at least "
                f"{settings.password_min_length} characters."
            )

        if (
            settings
            .password_require_letter
        ):
            if not re.search(
                r"[A-Za-z]",
                value,
            ):
                raise ValueError(
                    "Password must contain at least one letter."
                )

        if (
            settings
            .password_require_number
        ):
            if not re.search(
                r"\d",
                value,
            ):
                raise ValueError(
                    "Password must contain at least one number."
                )

        if (
            settings
            .password_require_special
        ):
            if not re.search(
                r"[^A-Za-z0-9]",
                value,
            ):
                raise ValueError(
                    "Password must contain at least one special character."
                )

        return value

    @model_validator(
        mode="after"
    )
    def reset_passwords_match(
        self,
    ) -> "ResetPasswordRequest":
        if (
            self.new_password !=
            self.confirm_password
        ):
            raise ValueError(
                "New password and confirm password do not match."
            )

        return self


class ResetPasswordResponse(
    AuthSchema
):
    message: str
    success: bool = True


# =========================================================
# AUTHENTICATED USER / ME
# =========================================================

class CurrentUserResponse(
    AuthSchema
):
    user: UserPublic


# =========================================================
# SESSION OUTPUT
# =========================================================

class SessionPublic(AuthSchema):
    id: uuid.UUID

    device_name: str | None = None
    user_agent: str | None = None
    ip_address: str | None = None

    expires_at: datetime

    last_used_at:datetime | None = None

    revoked_at:datetime | None = None

    created_at: datetime


class SessionsResponse(AuthSchema):
    sessions: list[
        SessionPublic
    ]

    total: int = Field(
        ge=0,
    )


# =========================================================
# OAUTH
# =========================================================

class OAuthCallbackRequest(
    AuthSchema
):
    code: str = Field(
        min_length=1,
        max_length=4096,
    )

    state: str = Field(
        min_length=20,
        max_length=8192,
    )

    @field_validator(
        "code",
        "state",
    )
    @classmethod
    def validate_oauth_callback_value(
        cls,
        value: str,
    ) -> str:
        normalized = (
            value.strip()
        )

        if not normalized:
            raise ValueError(
                "OAuth callback value cannot be empty."
            )

        return normalized


class OAuthAuthorizationResponse(
    AuthSchema
):
    provider:ExternalAuthProvider

    authorization_url: str = Field(
        min_length=1,
    )


class OAuthIdentityPublic(
    AuthSchema
):
    provider:ExternalAuthProvider

    provider_email:EmailStr | None = None

    provider_username:str | None = None

    provider_avatar_url:str | None = None

    linked_at: datetime


class OAuthCallbackResponse(
    AuthSchema
):
    access_token: str
    refresh_token: str

    token_type: TokenType = (
        "bearer"
    )

    expires_in: int = Field(
        gt=0,
    )

    user: UserPublic

    provider:ExternalAuthProvider

    is_new_user: bool

    intent:OAuthIntent

    remember_me: bool = False


class OAuthExchangeRequest(
    AuthSchema
):
    code: str = Field(
        min_length=20,
        max_length=512,
    )

    @field_validator(
        "code"
    )
    @classmethod
    def validate_exchange_code(
        cls,
        value: str,
    ) -> str:
        normalized = (
            value.strip()
        )

        if not normalized:
            raise ValueError(
                "OAuth exchange code cannot be empty."
            )

        return normalized


class OAuthExchangeResponse(
    OAuthCallbackResponse
):
    pass


# =========================================================
# GENERIC AUTH MESSAGE
# =========================================================

class AuthMessageResponse(
    AuthSchema
):
    message: str
    success: bool = True


# =========================================================
# PUBLIC EXPORTS
# =========================================================

__all__ = [
    "AuthProvider",
    "ExternalAuthProvider",
    "TokenType",
    "OAuthIntent",
    "UserPublic",
    "SignupRequest",
    "SignupResponse",
    "VerifyEmailRequest",
    "ResendVerificationRequest",
    "EmailVerificationResponse",
    "LoginRequest",
    "TokenResponse",
    "RefreshTokenRequest",
    "RefreshTokenResponse",
    "LogoutRequest",
    "LogoutResponse",
    "LogoutAllResponse",
    "ForgotPasswordRequest",
    "ForgotPasswordResponse",
    "VerifyResetOTPRequest",
    "VerifyResetOTPResponse",
    "ResetPasswordRequest",
    "ResetPasswordResponse",
    "CurrentUserResponse",
    "SessionPublic",
    "SessionsResponse",
    "OAuthCallbackRequest",
    "OAuthAuthorizationResponse",
    "OAuthIdentityPublic",
    "OAuthCallbackResponse",
    "OAuthExchangeRequest",
    "OAuthExchangeResponse",
    "AuthMessageResponse",
]