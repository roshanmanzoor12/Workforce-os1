from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.config import settings
from app.core.database import get_control_db
from app.db.base import Base
from app.main import app

from app.modules.auth import models as auth_models  # noqa: F401

import app.modules.auth.email_verification as email_verification_module
import app.modules.auth.password_reset as password_reset_module
import app.modules.auth.service as auth_service_module


# =========================================================
# CONSTANTS
# =========================================================

TEST_DATABASE_NAME = "workforce_test"

TEST_BASE_URL = "http://testserver"

FIXED_TEST_OTP = "123456"


# =========================================================
# DATABASE URL HELPERS
# =========================================================


def get_control_database_url() -> URL:
    return make_url(
        settings.control_database_url
    )


def get_test_database_url() -> URL:
    control_url = get_control_database_url()

    test_url = control_url.set(
        database=TEST_DATABASE_NAME
    )

    if test_url.database == control_url.database:
        raise RuntimeError(
            "Test database must not match workforce_control."
        )

    return test_url


def get_admin_database_url() -> URL:
    control_url = get_control_database_url()

    return control_url.set(
        drivername="postgresql+psycopg",
        database="postgres",
    )


# =========================================================
# SAFETY
# =========================================================


def assert_safe_test_database() -> None:
    test_url = get_test_database_url()

    if test_url.database != TEST_DATABASE_NAME:
        raise RuntimeError(
            f"Unsafe pytest database: {test_url.database}"
        )

    if test_url.database == "workforce_control":
        raise RuntimeError(
            "Refusing to run pytest against workforce_control."
        )


# =========================================================
# CREATE TEST DATABASE
# =========================================================


def create_test_database() -> None:
    assert_safe_test_database()

    admin_engine = create_engine(
        get_admin_database_url(),
        isolation_level="AUTOCOMMIT",
        pool_pre_ping=True,
    )

    try:
        with admin_engine.connect() as connection:

            connection.execute(
                text(
                    """
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = :database_name
                      AND pid <> pg_backend_pid()
                    """
                ),
                {
                    "database_name": TEST_DATABASE_NAME,
                },
            )

            connection.execute(
                text(
                    f'DROP DATABASE IF EXISTS "{TEST_DATABASE_NAME}"'
                )
            )

            connection.execute(
                text(
                    f'CREATE DATABASE "{TEST_DATABASE_NAME}"'
                )
            )

    finally:
        admin_engine.dispose()


def drop_test_database() -> None:
    assert_safe_test_database()

    admin_engine = create_engine(
        get_admin_database_url(),
        isolation_level="AUTOCOMMIT",
        pool_pre_ping=True,
    )

    try:
        with admin_engine.connect() as connection:

            connection.execute(
                text(
                    """
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = :database_name
                      AND pid <> pg_backend_pid()
                    """
                ),
                {
                    "database_name": TEST_DATABASE_NAME,
                },
            )

            connection.execute(
                text(
                    f'DROP DATABASE IF EXISTS "{TEST_DATABASE_NAME}"'
                )
            )

    finally:
        admin_engine.dispose()


# =========================================================
# DATABASE SESSION LIFECYCLE
# =========================================================


@pytest.fixture(
    scope="session",
    autouse=True,
)
def test_database_lifecycle():
    """
    Create one clean PostgreSQL database for the full pytest run.

    Async SQLAlchemy engines are NOT session-scoped because
    pytest-asyncio may create different event loops between tests.
    """

    create_test_database()

    yield

    drop_test_database()


# =========================================================
# FUNCTION-SCOPED ASYNC ENGINE
# =========================================================


@pytest_asyncio.fixture
async def test_engine(
    test_database_lifecycle,
) -> AsyncGenerator[AsyncEngine, None]:
    """
    Create a fresh async SQLAlchemy engine for each test.

    NullPool is intentional.

    asyncpg connections are tied to the event loop that created
    them. Reusing pooled asyncpg connections across pytest loops
    causes:

        Future attached to a different loop
        Event loop is closed

    A function-scoped engine + NullPool prevents that.
    """

    engine = create_async_engine(
        get_test_database_url(),
        echo=False,
        poolclass=NullPool,
    )

    async with engine.begin() as connection:
        await connection.run_sync(
            Base.metadata.create_all
        )

    try:
        yield engine

    finally:
        await engine.dispose()


# =========================================================
# DATABASE CLEANUP
# =========================================================


@pytest_asyncio.fixture(
    autouse=True,
)
async def clean_database(
    test_engine: AsyncEngine,
):
    """
    Start each test with empty control-database tables.
    """

    async with test_engine.begin() as connection:

        for table in reversed(
            Base.metadata.sorted_tables
        ):
            await connection.execute(
                table.delete()
            )

    yield

    async with test_engine.begin() as connection:

        for table in reversed(
            Base.metadata.sorted_tables
        ):
            await connection.execute(
                table.delete()
            )


# =========================================================
# SESSION FACTORY
# =========================================================


@pytest.fixture
def test_session_factory(
    test_engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:

    return async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


# =========================================================
# DIRECT DB SESSION
# =========================================================


@pytest_asyncio.fixture
async def db_session(
    test_session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:

    async with test_session_factory() as session:

        try:
            yield session

        finally:
            await session.rollback()


# =========================================================
# FASTAPI DATABASE OVERRIDE
# =========================================================


@pytest_asyncio.fixture(
    autouse=True,
)
async def override_control_database(
    test_session_factory: async_sessionmaker[AsyncSession],
):
    """
    Force FastAPI API requests to use workforce_test.
    """

    async def override_get_control_db():
        async with test_session_factory() as session:

            try:
                yield session

            except Exception:
                await session.rollback()
                raise

            finally:
                await session.close()

    app.dependency_overrides[
        get_control_db
    ] = override_get_control_db

    yield

    app.dependency_overrides.pop(
        get_control_db,
        None,
    )


# =========================================================
# FAKE REDIS RATE LIMITING
# =========================================================


class FakeAuthRateLimiter:

    def __init__(self) -> None:
        self.values: dict[str, int] = {}

    async def increment(
        self,
        key: str,
        amount: int = 1,
        expire_seconds: int | None = None,
        **kwargs: Any,
    ) -> int:

        self.values[key] = (
            self.values.get(
                key,
                0,
            )
            + amount
        )

        return self.values[key]

    def clear(self) -> None:
        self.values.clear()


@pytest.fixture(
    autouse=True,
)
def fake_auth_rate_limiter(
    monkeypatch: pytest.MonkeyPatch,
):

    limiter = FakeAuthRateLimiter()

    monkeypatch.setattr(
        auth_service_module,
        "redis_increment",
        limiter.increment,
    )

    yield limiter

    limiter.clear()


# =========================================================
# FIXED OTP FOR TESTS
# =========================================================


@pytest.fixture(
    autouse=True,
)
def deterministic_otp(
    monkeypatch: pytest.MonkeyPatch,
):

    monkeypatch.setattr(
        email_verification_module,
        "generate_otp",
        lambda: FIXED_TEST_OTP,
    )

    monkeypatch.setattr(
        password_reset_module,
        "generate_otp",
        lambda: FIXED_TEST_OTP,
    )

    return FIXED_TEST_OTP


# =========================================================
# DISABLE SMTP
# =========================================================


@pytest.fixture(
    autouse=True,
)
def disable_real_email(
    monkeypatch: pytest.MonkeyPatch,
):

    monkeypatch.setattr(
        settings,
        "email_enabled",
        False,
    )


# =========================================================
# HTTP CLIENT
# =========================================================


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:

    transport = ASGITransport(
        app=app
    )

    async with AsyncClient(
        transport=transport,
        base_url=TEST_BASE_URL,
        follow_redirects=True,
    ) as http_client:

        yield http_client


# =========================================================
# TEST USER FIXTURES
# =========================================================


@pytest.fixture
def test_user_payload() -> dict[str, Any]:
    """
    Use a real syntactically valid public-style domain.

    Do not use .local because EmailStr/email-validator rejects
    special-use domains.
    """

    return {
        "email": "test.auth@example.com",
        "username": "testauthuser",
        "password": "StrongPassword123!",
        "confirm_password": "StrongPassword123!",
        "first_name": "Test",
        "last_name": "User",
    }


@pytest.fixture
def second_test_user_payload() -> dict[str, Any]:

    return {
        "email": "second.auth@example.com",
        "username": "secondauthuser",
        "password": "AnotherStrongPassword123!",
        "confirm_password": "AnotherStrongPassword123!",
        "first_name": "Second",
        "last_name": "User",
    }


# =========================================================
# HELPER FUNCTIONS
# =========================================================


async def signup_user(
    client: AsyncClient,
    payload: dict[str, Any],
) -> dict[str, Any]:

    response = await client.post(
        "/api/v1/auth/signup",
        json=payload,
    )

    assert response.status_code == 201, (
        f"Signup failed: "
        f"{response.status_code} "
        f"{response.text}"
    )

    return response.json()


async def verify_user_email(
    client: AsyncClient,
    email: str,
    *,
    otp: str = FIXED_TEST_OTP,
) -> dict[str, Any]:

    response = await client.post(
        "/api/v1/auth/verify-email",
        json={
            "email": email,
            "otp": otp,
        },
    )

    assert response.status_code == 200, (
        f"Verification failed: "
        f"{response.status_code} "
        f"{response.text}"
    )

    return response.json()


async def login_user(
    client: AsyncClient,
    identifier: str,
    password: str,
    *,
    remember_me: bool = False,
) -> dict[str, Any]:

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "identifier": identifier,
            "password": password,
            "remember_me": remember_me,
        },
    )

    assert response.status_code == 200, (
        f"Login failed: "
        f"{response.status_code} "
        f"{response.text}"
    )

    return response.json()


async def create_verified_user(
    client: AsyncClient,
    payload: dict[str, Any],
) -> dict[str, Any]:

    await signup_user(
        client,
        payload,
    )

    return await verify_user_email(
        client,
        payload["email"],
    )


async def create_logged_in_user(
    client: AsyncClient,
    payload: dict[str, Any],
) -> dict[str, Any]:

    await create_verified_user(
        client,
        payload,
    )

    return await login_user(
        client,
        payload["email"],
        payload["password"],
    )


def bearer_headers(
    access_token: str,
) -> dict[str, str]:

    return {
        "Authorization": (
            f"Bearer {access_token}"
        )
    }


# =========================================================
# HELPER FIXTURES
# =========================================================


@pytest.fixture
def signup_helper():
    return signup_user


@pytest.fixture
def verify_email_helper():
    return verify_user_email


@pytest.fixture
def login_helper():
    return login_user


@pytest.fixture
def create_verified_user_helper():
    return create_verified_user


@pytest.fixture
def create_logged_in_user_helper():
    return create_logged_in_user


@pytest.fixture
def bearer_headers_helper():
    return bearer_headers