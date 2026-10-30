from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    create_async_engine,
)

from app.db.tenant import (
    SUPPORTED_TENANT_CLUSTER_KEY,
    TenantDatabaseConfigurationError,
    build_tenant_database_url,
    get_primary_database_url,
    validate_tenant_cluster_key,
    validate_tenant_database_name,
)


# =========================================================
# CONSTANTS
# =========================================================

POSTGRES_MAINTENANCE_DATABASE = "postgres"


# =========================================================
# ERRORS
# =========================================================


class TenantDatabaseProvisioningError(RuntimeError):
    """
    Raised when WorkforceOS cannot provision a physical
    PostgreSQL tenant database.

    Detailed database credentials must never be included in
    public API error messages.
    """

    pass


# =========================================================
# RESULT
# =========================================================


@dataclass(frozen=True, slots=True)
class TenantProvisioningResult:
    """
    Result of an idempotent physical tenant provisioning attempt.
    """

    database_name: str
    cluster_key: str
    created: bool
    already_existed: bool


# =========================================================
# TRUSTED ADMIN URL
# =========================================================


def build_postgres_admin_url(
    *,
    cluster_key: str = SUPPORTED_TENANT_CLUSTER_KEY,
) -> URL:
    """
    Build the trusted PostgreSQL maintenance connection URL.

    The control database URL provides the trusted:

    - driver
    - hostname
    - port
    - username
    - password
    - query parameters

    Only the database component is changed to PostgreSQL's
    maintenance database.

    No client-controlled URL is accepted.
    """

    validate_tenant_cluster_key(
        cluster_key
    )

    base_url = get_primary_database_url()

    return base_url.set(
        database=POSTGRES_MAINTENANCE_DATABASE
    )


# =========================================================
# ADMIN ENGINE
# =========================================================


def create_postgres_admin_engine(
    *,
    cluster_key: str = SUPPORTED_TENANT_CLUSTER_KEY,
) -> AsyncEngine:
    """
    Create a short-lived PostgreSQL administration engine.

    CREATE DATABASE cannot execute inside a normal transaction,
    therefore the engine uses AUTOCOMMIT isolation.

    This engine should be disposed immediately after the
    provisioning operation.
    """

    admin_url = build_postgres_admin_url(
        cluster_key=cluster_key
    )

    return create_async_engine(
        admin_url,
        isolation_level="AUTOCOMMIT",
        pool_pre_ping=True,
    )


# =========================================================
# SAFE IDENTIFIER QUOTING
# =========================================================


def quote_postgres_identifier(
    identifier: str,
) -> str:
    """
    Quote an already validated PostgreSQL identifier.

    Important:

    This helper is not a general-purpose sanitizer.

    Tenant database names must first pass
    validate_tenant_database_name(), which permits only:

        tenant_<32 lowercase hexadecimal characters>

    PostgreSQL identifiers cannot be supplied through normal
    SQL bind parameters, so strict validation occurs before
    quoting.
    """

    trusted_name = validate_tenant_database_name(
        identifier
    )

    return (
        '"'
        + trusted_name.replace(
            '"',
            '""',
        )
        + '"'
    )


# =========================================================
# DATABASE EXISTS
# =========================================================


async def tenant_database_exists(
    database_name: str,
    *,
    cluster_key: str = SUPPORTED_TENANT_CLUSTER_KEY,
) -> bool:
    """
    Check pg_database for one trusted tenant database identity.

    The database name is used as a normal SQL value here and can
    therefore be safely parameter-bound.
    """

    trusted_database_name = (
        validate_tenant_database_name(
            database_name
        )
    )

    trusted_cluster_key = (
        validate_tenant_cluster_key(
            cluster_key
        )
    )

    engine = create_postgres_admin_engine(
        cluster_key=trusted_cluster_key
    )

    try:
        async with engine.connect() as connection:
            result = await connection.execute(
                text(
                    """
                    SELECT 1
                    FROM pg_database
                    WHERE datname = :database_name
                    LIMIT 1
                    """
                ),
                {
                    "database_name": trusted_database_name,
                },
            )

            return result.scalar_one_or_none() is not None

    except TenantDatabaseConfigurationError:
        raise

    except Exception as exc:
        raise TenantDatabaseProvisioningError(
            "Unable to inspect tenant database state."
        ) from exc

    finally:
        await engine.dispose()


# =========================================================
# CREATE DATABASE
# =========================================================


async def create_tenant_database(
    database_name: str,
    *,
    cluster_key: str = SUPPORTED_TENANT_CLUSTER_KEY,
) -> TenantProvisioningResult:
    """
    Idempotently create one physical PostgreSQL tenant database.

    Correct trusted flow:

        workspace membership authorized
            ↓
        TenantDatabaseRegistry resolved
            ↓
        database_name taken from trusted control DB
            ↓
        strict tenant name validation
            ↓
        PostgreSQL pg_database existence check
            ↓
        CREATE DATABASE if absent

    Clients must never directly control database_name.

    If the tenant database already exists, the function succeeds
    without creating another database.
    """

    trusted_database_name = (
        validate_tenant_database_name(
            database_name
        )
    )

    trusted_cluster_key = (
        validate_tenant_cluster_key(
            cluster_key
        )
    )

    engine = create_postgres_admin_engine(
        cluster_key=trusted_cluster_key
    )

    try:
        async with engine.connect() as connection:
            existing = await connection.execute(
                text(
                    """
                    SELECT 1
                    FROM pg_database
                    WHERE datname = :database_name
                    LIMIT 1
                    """
                ),
                {
                    "database_name": trusted_database_name,
                },
            )

            if existing.scalar_one_or_none() is not None:
                return TenantProvisioningResult(
                    database_name=trusted_database_name,
                    cluster_key=trusted_cluster_key,
                    created=False,
                    already_existed=True,
                )

            quoted_database_name = (
                quote_postgres_identifier(
                    trusted_database_name
                )
            )

            await connection.exec_driver_sql(
                f"CREATE DATABASE {quoted_database_name}"
            )

    except TenantDatabaseConfigurationError:
        raise

    except Exception as exc:
        raise TenantDatabaseProvisioningError(
            "Unable to create tenant database."
        ) from exc

    finally:
        await engine.dispose()

    return TenantProvisioningResult(
        database_name=trusted_database_name,
        cluster_key=trusted_cluster_key,
        created=True,
        already_existed=False,
    )


# =========================================================
# CONNECTIVITY CHECK
# =========================================================


async def verify_tenant_database_connection(
    database_name: str,
    *,
    cluster_key: str = SUPPORTED_TENANT_CLUSTER_KEY,
) -> bool:
    """
    Verify that WorkforceOS can connect to a provisioned tenant DB.

    This performs only:

        SELECT 1

    It does not create schema objects and does not run migrations.
    """

    trusted_database_name = (
        validate_tenant_database_name(
            database_name
        )
    )

    trusted_cluster_key = (
        validate_tenant_cluster_key(
            cluster_key
        )
    )

    tenant_url = build_tenant_database_url(
        trusted_database_name,
        cluster_key=trusted_cluster_key,
    )

    engine = create_async_engine(
        tenant_url,
        pool_pre_ping=True,
    )

    try:
        async with engine.connect() as connection:
            result = await connection.execute(
                text(
                    "SELECT 1"
                )
            )

            return result.scalar_one() == 1

    except Exception as exc:
        raise TenantDatabaseProvisioningError(
            "Unable to connect to tenant database."
        ) from exc

    finally:
        await engine.dispose()


# =========================================================
# PROVISION AND VERIFY
# =========================================================


async def provision_tenant_database(
    database_name: str,
    *,
    cluster_key: str = SUPPORTED_TENANT_CLUSTER_KEY,
) -> TenantProvisioningResult:
    """
    Create the tenant database if necessary and verify connectivity.

    This function does not run tenant Alembic migrations yet.

    Schema migration is deliberately kept as a separate step so
    database creation and schema evolution remain independently
    testable and recoverable.
    """

    result = await create_tenant_database(
        database_name,
        cluster_key=cluster_key,
    )

    connected = await verify_tenant_database_connection(
        result.database_name,
        cluster_key=result.cluster_key,
    )

    if not connected:
        raise TenantDatabaseProvisioningError(
            "Tenant database was created but connectivity verification failed."
        )

    return result


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "POSTGRES_MAINTENANCE_DATABASE",
    "TenantDatabaseProvisioningError",
    "TenantProvisioningResult",
    "build_postgres_admin_url",
    "create_postgres_admin_engine",
    "quote_postgres_identifier",
    "tenant_database_exists",
    "create_tenant_database",
    "verify_tenant_database_connection",
    "provision_tenant_database",
]