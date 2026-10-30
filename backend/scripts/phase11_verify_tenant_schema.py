from __future__ import annotations

import asyncio
import os

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    create_async_engine,
)


EXPECTED_REVISION = "c2d3e4f5a6b7"

DEFAULT_TENANT_DATABASE = (
    "tenant_34527ffbe0944e5e89ee4cab97244fc3"
)


def database_url() -> str:
    database = os.getenv(
        "PHASE11_TENANT_DATABASE_NAME",
        DEFAULT_TENANT_DATABASE,
    )

    host = os.getenv(
        "POSTGRES_HOST",
        "localhost",
    )

    port = os.getenv(
        "POSTGRES_PORT",
        "5434",
    )

    user = os.getenv(
        "POSTGRES_USER",
        "postgres",
    )

    password = os.getenv(
        "POSTGRES_PASSWORD",
        "postgres",
    )

    return (
        "postgresql+asyncpg://"
        f"{user}:{password}"
        f"@{host}:{port}/{database}"
    )


async def main() -> None:
    engine = create_async_engine(
        database_url(),
        pool_pre_ping=True,
    )

    try:
        async with engine.connect() as connection:
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

            revision = (
                revision_result
                .scalar_one_or_none()
            )

            if revision != EXPECTED_REVISION:
                raise RuntimeError(
                    "Expected revision "
                    f"{EXPECTED_REVISION}, "
                    f"found {revision}."
                )

            print(
                f"PASS revision: {revision}"
            )

            tables_result = (
                await connection.execute(
                    text(
                        """
                        SELECT table_name
                        FROM information_schema.tables
                        WHERE table_schema = 'public'
                          AND table_name IN (
                            'website_observations',
                            'website_usage_intervals'
                          )
                        """
                    )
                )
            )

            tables = {
                row[0]
                for row
                in tables_result.fetchall()
            }

            required_tables = {
                "website_observations",
                "website_usage_intervals",
            }

            if tables != required_tables:
                raise RuntimeError(
                    "Phase 11 table verification failed."
                )

            print(
                "PASS website_observations"
            )

            print(
                "PASS website_usage_intervals"
            )

            index_result = (
                await connection.execute(
                    text(
                        """
                        SELECT indexname
                        FROM pg_indexes
                        WHERE schemaname = 'public'
                          AND tablename =
                              'website_usage_intervals'
                        """
                    )
                )
            )

            indexes = {
                row[0]
                for row
                in index_result.fetchall()
            }

            required_index = (
                "uq_website_usage_one_open_per_device"
            )

            if required_index not in indexes:
                raise RuntimeError(
                    "Missing Phase 11 open-interval index."
                )

            print(
                "PASS one-open-interval index"
            )

            privacy_result = (
                await connection.execute(
                    text(
                        """
                        SELECT COUNT(*)
                        FROM website_observations
                        WHERE page_url IS NOT NULL
                           OR page_title IS NOT NULL
                        """
                    )
                )
            )

            non_private_rows = int(
                privacy_result.scalar_one()
            )

            if non_private_rows != 0:
                print(
                    "WARNING existing Website Tracking "
                    "rows contain URL/title values."
                )

    finally:
        await engine.dispose()

    print(
        "PASS Phase 11 tenant schema verification"
    )


if __name__ == "__main__":
    asyncio.run(
        main()
    )