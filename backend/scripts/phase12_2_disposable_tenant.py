from __future__ import annotations

import argparse
import asyncio
import sys
import uuid
from pathlib import Path


ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

root_text = str(
    ROOT
)

if root_text not in sys.path:
    sys.path.insert(
        0,
        root_text,
    )


from sqlalchemy import text

from app.db.tenant import (
    dispose_tenant_engine,
    validate_tenant_database_name,
)

from app.db.tenant_provisioning import (
    create_postgres_admin_engine,
    create_tenant_database,
    quote_postgres_identifier,
    tenant_database_exists,
)

def generate_database_name() -> str:
    return (
        "tenant_"
        + uuid.uuid4().hex
    )


async def create_disposable_database(
    database_name: str | None = None,
) -> str:
    name = (
        database_name
        or generate_database_name()
    )

    trusted = (
        validate_tenant_database_name(
            name
        )
    )

    result = await (
        create_tenant_database(
            trusted
        )
    )

    print(
        "DISPOSABLE_DATABASE="
        + result.database_name
    )

    return result.database_name


async def drop_disposable_database(
    database_name: str,
) -> None:
    trusted = (
        validate_tenant_database_name(
            database_name
        )
    )

    try:
        await dispose_tenant_engine(
            trusted
        )
    except Exception:
        # Disposable cleanup should still attempt
        # administrative termination/drop.
        pass

    engine = (
        create_postgres_admin_engine()
    )

    quoted = (
        quote_postgres_identifier(
            trusted
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
                        trusted
                    ),
                },
            )

            await (
                connection
                .exec_driver_sql(
                    (
                        "DROP DATABASE "
                        "IF EXISTS "
                        f"{quoted}"
                    )
                )
            )

    finally:
        await engine.dispose()

    print(
        "DROPPED_DATABASE="
        + trusted
    )


async def database_exists(
    database_name: str,
) -> bool:
    return await (
        tenant_database_exists(
            database_name
        )
    )


async def async_main() -> None:
    parser = argparse.ArgumentParser()

    sub = (
        parser
        .add_subparsers(
            dest="command",
            required=True,
        )
    )

    create_parser = (
        sub.add_parser(
            "create"
        )
    )

    create_parser.add_argument(
        "--name",
        default=None,
    )

    drop_parser = (
        sub.add_parser(
            "drop"
        )
    )

    drop_parser.add_argument(
        "name"
    )

    exists_parser = (
        sub.add_parser(
            "exists"
        )
    )

    exists_parser.add_argument(
        "name"
    )

    args = parser.parse_args()

    if args.command == "create":
        await create_disposable_database(
            args.name
        )

    elif args.command == "drop":
        await drop_disposable_database(
            args.name
        )

    elif args.command == "exists":
        exists = await database_exists(
            args.name
        )

        print(
            "true"
            if exists
            else "false"
        )


if __name__ == "__main__":
    asyncio.run(
        async_main()
    )