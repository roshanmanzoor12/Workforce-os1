from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


EXPECTED_REVISION = "c2d3e4f5a6b7"

EXPECTED_PREVIOUS_REVISION = "b1c2d3e4f5a6"

DEFAULT_TENANT_DATABASE = (
    "tenant_34527ffbe0944e5e89ee4cab97244fc3"
)


def get_backend_root() -> Path:
    return Path(__file__).resolve().parents[1]


def get_tenant_database_name() -> str:
    database_name = os.getenv(
        "PHASE11_TENANT_DATABASE_NAME",
        DEFAULT_TENANT_DATABASE,
    ).strip()

    if not database_name:
        raise RuntimeError(
            "Tenant database name is empty."
        )

    if not database_name.startswith(
        "tenant_"
    ):
        raise RuntimeError(
            "Tenant database name must begin with 'tenant_'."
        )

    return database_name


def get_async_database_url(
    database_name: str,
) -> str:
    host = os.getenv(
        "POSTGRES_HOST",
        "localhost",
    ).strip()

    port = os.getenv(
        "POSTGRES_PORT",
        "5434",
    ).strip()

    user = os.getenv(
        "POSTGRES_USER",
        "postgres",
    ).strip()

    password = os.getenv(
        "POSTGRES_PASSWORD",
        "postgres",
    )

    return (
        "postgresql+asyncpg://"
        f"{user}:{password}"
        f"@{host}:{port}"
        f"/{database_name}"
    )


async def read_current_revision_async(
    database_url: str,
) -> str | None:
    engine = create_async_engine(
        database_url,
        pool_pre_ping=True,
    )

    try:
        async with engine.connect() as connection:
            table_exists_result = (
                await connection.execute(
                    text(
                        """
                        SELECT EXISTS (
                            SELECT 1
                            FROM information_schema.tables
                            WHERE table_schema = 'public'
                              AND table_name = 'alembic_version'
                        )
                        """
                    )
                )
            )

            table_exists = bool(
                table_exists_result.scalar_one()
            )

            if not table_exists:
                return None

            revision_result = (
                await connection.execute(
                    text(
                        """
                        SELECT version_num
                        FROM alembic_version
                        LIMIT 1
                        """
                    )
                )
            )

            return (
                revision_result
                .scalar_one_or_none()
            )

    finally:
        await engine.dispose()


def read_current_revision(
    database_url: str,
) -> str | None:
    return asyncio.run(
        read_current_revision_async(
            database_url
        )
    )


def get_alembic_config_path() -> Path:
    config_path = (
        get_backend_root()
        / "alembic.tenant.ini"
    )

    if not config_path.exists():
        raise RuntimeError(
            "Tenant Alembic configuration was not found: "
            f"{config_path}"
        )

    return config_path


def run_alembic_upgrade(
    database_name: str,
) -> None:
    backend_root = get_backend_root()

    config_path = (
        get_alembic_config_path()
    )

    print(
        f"Alembic config: {config_path}"
    )

    print(
        f"Alembic tenant: {database_name}"
    )

    print(
        "Launching tenant Alembic in separate process..."
    )

    environment = os.environ.copy()

    command = [
        sys.executable,
        "-m",
        "alembic",
        "-c",
        str(config_path),
        "-x",
        f"database_name={database_name}",
        "upgrade",
        EXPECTED_REVISION,
    ]

    result = subprocess.run(
        command,
        cwd=str(backend_root),
        env=environment,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Tenant Alembic subprocess failed "
            f"with exit code {result.returncode}."
        )


def main() -> None:
    database_name = (
        get_tenant_database_name()
    )

    database_url = (
        get_async_database_url(
            database_name
        )
    )

    print(
        f"Tenant database: {database_name}"
    )

    revision_before = (
        read_current_revision(
            database_url
        )
    )

    print(
        f"Revision before: {revision_before}"
    )

    if revision_before == EXPECTED_REVISION:
        print(
            "Tenant is already at Phase 11 revision."
        )

        print(
            "PASS Phase 11 tenant migration"
        )

        return

    if (
        revision_before
        != EXPECTED_PREVIOUS_REVISION
    ):
        raise RuntimeError(
            "Unexpected tenant revision. "
            f"Expected {EXPECTED_PREVIOUS_REVISION}, "
            f"found {revision_before}."
        )

    run_alembic_upgrade(
        database_name
    )

    revision_after = (
        read_current_revision(
            database_url
        )
    )

    print(
        f"Revision after: {revision_after}"
    )

    if revision_after != EXPECTED_REVISION:
        raise RuntimeError(
            "Phase 11 migration command completed "
            "but tenant revision is incorrect. "
            f"Expected {EXPECTED_REVISION}, "
            f"found {revision_after}."
        )

    print(
        "PASS Phase 11 tenant migration"
    )


if __name__ == "__main__":
    main()