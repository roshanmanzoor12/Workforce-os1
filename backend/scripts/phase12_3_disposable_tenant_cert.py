from __future__ import annotations

import asyncio
import subprocess
import sys
import uuid

from sqlalchemy import (
    text,
)

from app.db.tenant_provisioning import (
    create_postgres_admin_engine,
    quote_postgres_identifier,
)


PAYROLL_FOUNDATION = (
    "o5j6k7l8m9n0"
)


PAYSLIP_HEAD = (
    "p6k7l8m9n0o1"
)


DATABASE_NAME = (
    "tenant_"
    + uuid.uuid4().hex
)


async def create_database() -> None:
    engine = (
        create_postgres_admin_engine()
    )

    quoted = (
        quote_postgres_identifier(
            DATABASE_NAME
        )
    )

    try:
        async with engine.connect() as connection:
            await (
                connection
                .exec_driver_sql(
                    f"CREATE DATABASE {quoted}"
                )
            )

    finally:
        await engine.dispose()


async def drop_database() -> None:
    engine = (
        create_postgres_admin_engine()
    )

    quoted = (
        quote_postgres_identifier(
            DATABASE_NAME
        )
    )

    try:
        async with engine.connect() as connection:
            await connection.execute(
                text(
                    """
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = :database_name
                      AND pid <> pg_backend_pid()
                    """
                ),
                {
                    "database_name": (
                        DATABASE_NAME
                    ),
                },
            )

            await (
                connection
                .exec_driver_sql(
                    f"DROP DATABASE IF EXISTS {quoted}"
                )
            )

    finally:
        await engine.dispose()


def alembic(
    *arguments: str,
) -> None:
    command = [
        sys.executable,
        "-m",
        "alembic",
        "-c",
        "alembic.tenant.ini",
        "-x",
        (
            "database_name="
            + DATABASE_NAME
        ),
        *arguments,
    ]

    print(
        "RUN",
        " ".join(
            command
        ),
    )

    subprocess.run(
        command,
        check=True,
    )


def main() -> None:
    print(
        "Disposable tenant:",
        DATABASE_NAME,
    )

    try:
        asyncio.run(
            create_database()
        )

        print()
        print(
            "[1/3] Upgrade to Payslip head"
        )

        alembic(
            "upgrade",
            PAYSLIP_HEAD,
        )

        print()
        print(
            "[2/3] Downgrade to Payroll foundation"
        )

        alembic(
            "downgrade",
            PAYROLL_FOUNDATION,
        )

        print()
        print(
            "[3/3] Re-upgrade to Payslip head"
        )

        alembic(
            "upgrade",
            PAYSLIP_HEAD,
        )

        print()
        print(
            "PASS disposable Payroll migration certificate"
        )

    finally:
        print()
        print(
            "Dropping disposable tenant..."
        )

        asyncio.run(
            drop_database()
        )


if __name__ == "__main__":
    main()