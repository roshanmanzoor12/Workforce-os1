from __future__ import annotations

import asyncio
import os

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


DEFAULT_DATABASE = (
    "tenant_34527ffbe0944e5e89ee4cab97244fc3"
)


def get_database_url() -> str:
    database = os.getenv(
        "PHASE11_TENANT_DATABASE_NAME",
        DEFAULT_DATABASE,
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
        f"@{host}:{port}"
        f"/{database}"
    )


async def main() -> None:
    engine = create_async_engine(
        get_database_url(),
        pool_pre_ping=True,
    )

    try:
        async with engine.connect() as connection:
            observation_result = await connection.execute(
                text(
                    """
                    SELECT
                        id,
                        browser_name,
                        browser_process_name,
                        domain,
                        normalized_domain,
                        page_url,
                        page_title,
                        observed_at
                    FROM website_observations
                    ORDER BY observed_at DESC
                    LIMIT 20
                    """
                )
            )

            observations = (
                observation_result
                .mappings()
                .all()
            )

            print("")
            print(
                "Latest website observations:"
            )

            if not observations:
                raise RuntimeError(
                    "No Website Tracking observations found."
                )

            for row in observations:
                print(
                    " | ".join(
                        [
                            str(
                                row["observed_at"]
                            ),
                            str(
                                row["browser_process_name"]
                            ),
                            str(
                                row["normalized_domain"]
                            ),
                        ]
                    )
                )

                if row["page_url"] is not None:
                    raise RuntimeError(
                        "Privacy gate failed: "
                        "page_url was persisted."
                    )

                if row["page_title"] is not None:
                    raise RuntimeError(
                        "Privacy gate failed: "
                        "page_title was persisted."
                    )

            interval_result = await connection.execute(
                text(
                    """
                    SELECT
                        id,
                        domain,
                        normalized_domain,
                        status,
                        duration_seconds,
                        started_at,
                        last_observed_at,
                        ended_at
                    FROM website_usage_intervals
                    ORDER BY started_at DESC
                    LIMIT 20
                    """
                )
            )

            intervals = (
                interval_result
                .mappings()
                .all()
            )

            print("")
            print(
                "Latest website intervals:"
            )

            if not intervals:
                raise RuntimeError(
                    "No Website Tracking intervals found."
                )

            for row in intervals:
                print(
                    " | ".join(
                        [
                            str(
                                row["started_at"]
                            ),
                            str(
                                row["normalized_domain"]
                            ),
                            str(
                                row["status"]
                            ),
                            str(
                                row["duration_seconds"]
                            ),
                        ]
                    )
                )

            print("")
            print(
                f"PASS observations: {len(observations)}"
            )

            print(
                f"PASS intervals: {len(intervals)}"
            )

            print(
                "PASS URL/title privacy defaults"
            )

    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(
        main()
    )