from __future__ import annotations

import asyncio
import os

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


DEFAULT_DATABASE = (
    "tenant_34527ffbe0944e5e89ee4cab97244fc3"
)


def database_url() -> str:
    database = os.getenv(
        "PHASE11_TENANT_DATABASE_NAME",
        DEFAULT_DATABASE,
    )

    return (
        "postgresql+asyncpg://"
        f"{os.getenv('POSTGRES_USER', 'postgres')}:"
        f"{os.getenv('POSTGRES_PASSWORD', 'postgres')}"
        f"@{os.getenv('POSTGRES_HOST', 'localhost')}:"
        f"{os.getenv('POSTGRES_PORT', '5434')}"
        f"/{database}"
    )


async def main() -> None:
    print(
        "Checking Phase 11 domain-switch evidence..."
    )

    engine = create_async_engine(
        database_url(),
        pool_pre_ping=True,
    )

    try:
        async with engine.connect() as connection:
            result = await connection.execute(
                text(
                    """
                    SELECT
                        normalized_domain,
                        status,
                        duration_seconds,
                        started_at,
                        last_observed_at,
                        ended_at
                    FROM website_usage_intervals
                    WHERE normalized_domain IN (
                        'github.com',
                        'youtube.com'
                    )
                    ORDER BY started_at DESC
                    LIMIT 20
                    """
                )
            )

            rows = (
                result
                .mappings()
                .all()
            )

            if not rows:
                raise RuntimeError(
                    "No GitHub/YouTube website intervals found."
                )

            github_rows = [
                row
                for row in rows
                if (
                    row["normalized_domain"]
                    == "github.com"
                )
            ]

            youtube_rows = [
                row
                for row in rows
                if (
                    row["normalized_domain"]
                    == "youtube.com"
                )
            ]

            print(
                f"github.com intervals: {len(github_rows)}"
            )

            print(
                f"youtube.com intervals: {len(youtube_rows)}"
            )

            print("")
            print(
                "Latest matching intervals:"
            )

            for row in rows[:10]:
                print(
                    " | ".join(
                        [
                            str(
                                row["normalized_domain"]
                            ),
                            str(
                                row["status"]
                            ),
                            str(
                                row["duration_seconds"]
                            ),
                            str(
                                row["started_at"]
                            ),
                        ]
                    )
                )

            if len(github_rows) < 2:
                raise RuntimeError(
                    "Expected at least two github.com intervals."
                )

            if len(youtube_rows) < 1:
                raise RuntimeError(
                    "Expected at least one youtube.com interval."
                )

            latest_three = [
                row["normalized_domain"]
                for row in rows[:3]
            ]

            print("")
            print(
                "Latest matching domains: "
                + " -> ".join(
                    latest_three
                )
            )

            expected_latest = [
                "github.com",
                "youtube.com",
                "github.com",
            ]

            if latest_three != expected_latest:
                print("")
                print(
                    "NOTE: GitHub and YouTube evidence exists, "
                    "but the three most recent matching intervals "
                    "are not the strict test sequence."
                )

                print(
                    "Run a fresh sequence:"
                )

                print(
                    "github.com -> youtube.com -> github.com"
                )

                raise RuntimeError(
                    "Latest domain-switch sequence is not "
                    "github.com -> youtube.com -> github.com."
                )

            print("")
            print(
                "PASS Phase 11 domain-switch evidence"
            )

    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(
        main()
    )