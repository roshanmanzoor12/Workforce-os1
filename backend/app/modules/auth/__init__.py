"""
WorkforceOS Authentication Module
=================================

PURPOSE
-------
This module owns WorkforceOS global authentication and identity.

Authentication is PLATFORM-GLOBAL.

A user authenticates once into WorkforceOS and can later belong to:

- one company as owner
- another company as employee
- another company as consultant
- multiple workspaces at the same time

Authentication must therefore NOT be tied directly to a tenant database.

The control database is the source of truth for:

- global users
- local authentication
- Google identities
- GitHub identities
- email verification
- password reset
- refresh sessions
- security state


SUPPORTED AUTHENTICATION
------------------------

Local authentication:

    email
        +
    password

OAuth:

    Google
    GitHub


AUTHENTICATION FLOWS
--------------------

Signup:

    signup
        ↓
    create global user
        ↓
    hash password
        ↓
    create email verification challenge
        ↓
    send OTP
        ↓
    verify email
        ↓
    activate verified account


Login:

    email / username
        ↓
    verify password
        ↓
    validate account status
        ↓
    create refresh session
        ↓
    issue access token
        ↓
    issue refresh token


Refresh:

    refresh token
        ↓
    validate JWT
        ↓
    validate stored refresh session
        ↓
    rotate refresh token
        ↓
    revoke previous token
        ↓
    issue new token pair


Logout:

    authenticated session
        ↓
    revoke current refresh session


Logout All:

    authenticated user
        ↓
    revoke every active refresh session


Forgot Password:

    email
        ↓
    password-reset challenge
        ↓
    OTP email
        ↓
    OTP verification
        ↓
    reset authorization
        ↓
    new password
        ↓
    revoke existing sessions


Google OAuth:

    WorkforceOS
        ↓
    Google authorization
        ↓
    callback
        ↓
    validate OAuth state
        ↓
    retrieve provider identity
        ↓
    locate/create global user
        ↓
    link identity
        ↓
    issue WorkforceOS session


GitHub OAuth:

    WorkforceOS
        ↓
    GitHub authorization
        ↓
    callback
        ↓
    validate OAuth state
        ↓
    retrieve provider identity
        ↓
    locate/create global user
        ↓
    link identity
        ↓
    issue WorkforceOS session


MODULE FILE RESPONSIBILITIES
----------------------------

__init__.py
    Public authentication-module exports.

router.py
    HTTP transport only.

    Responsibilities:
    - receive requests
    - validate FastAPI dependencies
    - call service methods
    - convert service results into responses

    Must NOT contain:
    - database queries
    - password logic
    - JWT implementation
    - OAuth business logic
    - OTP business logic


schemas.py
    Pydantic request/response DTOs.

    Examples:
    - SignupRequest
    - LoginRequest
    - TokenResponse
    - RefreshRequest
    - ForgotPasswordRequest
    - VerifyOTPRequest
    - ResetPasswordRequest
    - UserSessionResponse


models.py
    SQLAlchemy control-database ORM models.

    Authentication models may include:

    - User
    - AuthIdentity
    - RefreshSession
    - EmailVerificationChallenge
    - PasswordResetChallenge


repository.py
    Database access only.

    Responsibilities:
    - query users
    - query identities
    - query sessions
    - persist authentication records
    - revoke sessions

    Must NOT:
    - issue JWTs
    - decide login policy
    - send email
    - perform OAuth orchestration


service.py
    Authentication business orchestration.

    Responsibilities:
    - signup
    - login
    - refresh
    - logout
    - logout all
    - verify email
    - resend email verification
    - forgot password
    - verify reset OTP
    - reset password
    - account status checks
    - auth event generation


passwords.py
    Authentication password-policy layer.

    Uses cryptographic primitives from:

        app.core.security

    Responsibilities:
    - password-policy validation
    - password hashing wrapper
    - password verification wrapper
    - future password-history checks


tokens.py
    Authentication token/session policy layer.

    Uses:

        app.core.security

    Responsibilities:
    - access token creation
    - refresh token creation
    - refresh-session lifecycle
    - refresh rotation
    - token revocation
    - session validation


email_verification.py
    Email-verification challenge lifecycle.

    Responsibilities:
    - generate OTP
    - hash OTP
    - expiration
    - attempt limits
    - resend rules
    - successful verification


password_reset.py
    Password-reset challenge lifecycle.

    Responsibilities:
    - request reset
    - issue OTP
    - OTP verification
    - attempt limits
    - reset authorization
    - completion
    - session revocation


oauth_google.py
    Google OAuth implementation.

    Responsibilities:
    - authorization URL
    - OAuth state
    - callback validation
    - token exchange
    - profile retrieval
    - identity normalization


oauth_github.py
    GitHub OAuth implementation.

    Responsibilities:
    - authorization URL
    - OAuth state
    - callback validation
    - token exchange
    - user/email retrieval
    - identity normalization


permissions.py
    Authentication-related permission/dependency helpers.

    Examples:
    - current authenticated user
    - active user requirement
    - verified-email requirement
    - platform-account checks

    Workspace RBAC belongs to the later permissions/RBAC modules.


events.py
    Authentication domain events.

    Examples:
    - user_registered
    - email_verified
    - login_succeeded
    - login_failed
    - password_reset_requested
    - password_changed
    - session_revoked
    - oauth_identity_linked


CONTROL DATABASE OWNERSHIP
--------------------------

Authentication tables belong in:

    workforce_control

NOT:

    tenant_<workspace_uuid>

Reason:

A WorkforceOS person exists globally before workspace membership.


SECURITY RULES
--------------

1. Never store plaintext passwords.

2. Passwords use the shared secure hashing layer.

3. Never store plaintext OTPs.

4. Store a keyed hash/HMAC of OTP values.

5. OTPs must expire.

6. OTP attempts must be limited.

7. Login attempts must be rate-limited.

8. Password-reset requests must be rate-limited.

9. Verification resend operations must be rate-limited.

10. Access tokens must be short lived.

11. Refresh sessions must be server-revocable.

12. Refresh tokens should be rotated.

13. Logout must revoke the associated session.

14. Logout-all must revoke every active session.

15. Password reset should revoke previous sessions.

16. OAuth state must be validated.

17. OAuth provider IDs must be unique per provider.

18. Email ownership must never be assumed solely from unverified
    provider data.

19. Authentication must never accept a frontend-supplied arbitrary
    tenant database identifier.

20. Authentication must never bypass later workspace membership or
    RBAC checks.


TENANT BOUNDARY
---------------

Authentication answers:

    Who is this person?

Workspace membership answers:

    Which company can this person access?

RBAC answers:

    What can this person do in that company?

Tenant routing answers:

    Which company database should this request use?

These responsibilities must remain separate.


EXPECTED CONTROL-DATABASE RELATIONSHIPS
---------------------------------------

User
    |
    +---- AuthIdentity
    |
    +---- RefreshSession
    |
    +---- EmailVerificationChallenge
    |
    +---- PasswordResetChallenge
    |
    +---- later WorkspaceMembership


TESTING REQUIREMENTS
--------------------

Unit tests:

- password policy
- password hashing
- password verification
- token creation
- token decoding
- OTP generation
- OTP verification
- refresh rotation rules


Integration tests:

- create user
- unique email
- unique username
- identities
- sessions
- OTP challenge persistence
- password reset persistence


API tests:

- signup
- verification
- login
- refresh
- logout
- logout all
- forgot password
- reset OTP
- password reset
- /auth/me
- Google OAuth callbacks
- GitHub OAuth callbacks


Security tests:

- expired access token
- expired refresh token
- malformed token
- wrong token type
- revoked refresh session
- reused rotated refresh token
- invalid OTP
- expired OTP
- OTP attempt exhaustion
- disabled account
- unverified account where verification is required
- OAuth state mismatch
- duplicate provider identity


RBAC / TENANT TESTS
-------------------

Authentication itself is global, but later integration tests must prove:

- authentication cannot select arbitrary tenant databases
- authenticated user without membership cannot access workspace
- one workspace cannot access another workspace's tenant database
- OAuth login does not bypass membership validation
- platform authentication does not imply platform-admin permission


DEPENDENCY DIRECTION
--------------------

Correct:

    router
      ↓
    service
      ↓
    repository
      ↓
    SQLAlchemy

And:

    service
      ↓
    passwords / tokens / verification / reset / OAuth
      ↓
    app.core.security


Incorrect:

    router → SQLAlchemy directly
    repository → JWT generation
    model → service
    core.security → auth.service


PUBLIC MODULE API
-----------------

The public imports from this package should stay intentionally small.

As authentication files are implemented, stable public exports may be
added here.

Avoid importing unfinished modules from __init__.py because doing so can
cause circular imports during early development.
"""

__all__: list[str] = []