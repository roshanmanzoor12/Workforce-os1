from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_control_db
from app.core.exceptions import (
    AccountDisabled,
    AccountLocked,
    AuthenticationError,
    EmailNotVerified,
    InvalidToken,
    ResourceNotFound,
)
from app.core.logging import (
    get_logger,
    set_request_context,
)
from app.modules.auth.models import User
from app.modules.auth.repository import AuthRepository
from app.modules.auth.tokens import (
    AccessTokenClaims,
    validate_access_token,
)


logger = get_logger(__name__)


# =========================================================
# BEARER AUTH SCHEME
# =========================================================

bearer_scheme = HTTPBearer(
    auto_error=False,
)


# =========================================================
# TYPE ALIASES
# =========================================================

ControlDB = Annotated[
    AsyncSession,
    Depends(get_control_db),
]


BearerCredentials = Annotated[
    HTTPAuthorizationCredentials | None,
    Depends(bearer_scheme),
]


# =========================================================
# TOKEN EXTRACTION
# =========================================================

def extract_bearer_token(
    credentials: HTTPAuthorizationCredentials | None,
) -> str:
    """
    Extract bearer token from FastAPI HTTPBearer credentials.

    Raises:
        AuthenticationError
    """

    if credentials is None:
        raise AuthenticationError(
            "Authentication credentials are required."
        )

    if credentials.scheme.lower() != "bearer":
        raise AuthenticationError(
            "Bearer authentication is required."
        )

    token = credentials.credentials

    if not token:
        raise AuthenticationError(
            "Authentication token is missing."
        )

    return token


# =========================================================
# ACCESS TOKEN CLAIMS
# =========================================================

def authenticate_access_token(
    token: str,
) -> AccessTokenClaims:
    """
    Validate and normalize WorkforceOS access-token claims.

    This only validates global identity/session claims.

    It does NOT perform:
    - workspace membership checks
    - tenant routing
    - workspace RBAC
    """

    return validate_access_token(
        token
    )


# =========================================================
# LOAD AUTHENTICATED USER
# =========================================================

async def load_authenticated_user(
    *,
    repository: AuthRepository,
    claims: AccessTokenClaims,
) -> User:
    """
    Load global user referenced by validated JWT claims.

    Raises:
        InvalidToken
    """

    user = await repository.get_user_by_id(
        claims.user_id
    )

    if user is None:
        raise InvalidToken(
            "Authentication user no longer exists."
        )

    return user


# =========================================================
# ACCOUNT STATE VALIDATION
# =========================================================

def require_active_account(
    user: User,
) -> User:
    """
    Ensure global account is active.
    """

    if not user.is_active:
        raise AccountDisabled(
            "This WorkforceOS account is disabled."
        )

    return user


def require_unlocked_account(
    user: User,
) -> User:
    """
    Ensure account is not locked.
    """

    if user.is_locked:
        raise AccountLocked(
            "This WorkforceOS account is locked."
        )

    return user


def require_verified_email(
    user: User,
) -> User:
    """
    Require primary WorkforceOS email verification.
    """

    if not user.is_email_verified:
        raise EmailNotVerified(
            "Email verification is required."
        )

    return user


# =========================================================
# CURRENT USER DEPENDENCY
# =========================================================

async def get_current_user(
    credentials: BearerCredentials,
    db: ControlDB,
) -> User:
    """
    Main global authentication dependency.

    Flow:

        Authorization header
            ↓
        Bearer token
            ↓
        validate JWT
            ↓
        extract user_id/session_id
            ↓
        query workforce_control.users
            ↓
        ensure user exists
            ↓
        ensure active
            ↓
        ensure unlocked
            ↓
        return User

    Email verification is intentionally NOT automatically required
    here because some routes may need authenticated-but-unverified
    users.

    Routes requiring verification should use:

        get_current_verified_user
    """

    token = extract_bearer_token(
        credentials
    )

    claims = authenticate_access_token(
        token
    )

    repository = AuthRepository(
        db
    )

    user = await load_authenticated_user(
        repository=repository,
        claims=claims,
    )

    require_active_account(
        user
    )

    require_unlocked_account(
        user
    )

    # Add authenticated identity into logging context.
    set_request_context(
        user_id=str(user.id)
    )

    return user


# =========================================================
# VERIFIED USER DEPENDENCY
# =========================================================

async def get_current_verified_user(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> User:
    """
    Require:
    - valid access token
    - existing user
    - active account
    - unlocked account
    - verified email
    """

    require_verified_email(
        current_user
    )

    return current_user


# =========================================================
# OPTIONAL CURRENT USER
# =========================================================

async def get_optional_current_user(
    credentials: BearerCredentials,
    db: ControlDB,
) -> User | None:
    """
    Return authenticated user when a valid bearer token is supplied.

    Return None when no credentials are supplied.

    IMPORTANT:
    Invalid credentials still raise an authentication error.

    Useful later for:
    - public/private hybrid endpoints
    - invite pages
    - public app metadata
    """

    if credentials is None:
        return None

    return await get_current_user(
        credentials=credentials,
        db=db,
    )


# =========================================================
# CURRENT USER ID
# =========================================================

async def get_current_user_id(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> uuid.UUID:
    """
    Return authenticated global user UUID.
    """

    return current_user.id


# =========================================================
# VERIFIED USER ID
# =========================================================

async def get_current_verified_user_id(
    current_user: Annotated[
        User,
        Depends(get_current_verified_user),
    ],
) -> uuid.UUID:
    """
    Return verified authenticated user UUID.
    """

    return current_user.id


# =========================================================
# SESSION CLAIM DEPENDENCY
# =========================================================

async def get_current_access_claims(
    credentials: BearerCredentials,
) -> AccessTokenClaims:
    """
    Return validated access-token claims without loading the user.

    Use sparingly.

    Most protected routes should use get_current_user because
    database-backed account state must remain authoritative.
    """

    token = extract_bearer_token(
        credentials
    )

    return authenticate_access_token(
        token
    )


# =========================================================
# SESSION ID DEPENDENCY
# =========================================================

async def get_current_session_id(
    claims: Annotated[
        AccessTokenClaims,
        Depends(get_current_access_claims),
    ],
) -> uuid.UUID:
    """
    Return current authentication session UUID.
    """

    return claims.session_id


# =========================================================
# PUBLIC EXPORTS
# =========================================================

__all__ = [
    "bearer_scheme",
    "ControlDB",
    "BearerCredentials",
    "extract_bearer_token",
    "authenticate_access_token",
    "load_authenticated_user",
    "require_active_account",
    "require_unlocked_account",
    "require_verified_email",
    "get_current_user",
    "get_current_verified_user",
    "get_optional_current_user",
    "get_current_user_id",
    "get_current_verified_user_id",
    "get_current_access_claims",
    "get_current_session_id",
]