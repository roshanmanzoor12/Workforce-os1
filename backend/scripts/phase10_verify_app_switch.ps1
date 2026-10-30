#Requires -Version 5.1

param(
    [string]$TenantDatabaseName =
        "tenant_34527ffbe0944e5e89ee4cab97244fc3",

    [int]$MaximumAgeSeconds =
        300
)

$ErrorActionPreference = "Stop"

$Python =
    "C:\workforce-os\.venv\Scripts\python.exe"

$EnvironmentFile =
    "C:\workforce-os\.env"

$Runner = @'
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path

import asyncpg


ENV_PATH = Path(r"__ENV_PATH__")
DATABASE_NAME = "__DATABASE_NAME__"
MAXIMUM_AGE_SECONDS = __MAXIMUM_AGE_SECONDS__


def load_env(
    path: Path,
) -> dict[str, str]:
    values: dict[str, str] = {}

    for raw_line in path.read_text(
        encoding="utf-8-sig"
    ).splitlines():
        line = raw_line.strip()

        if (
            not line
            or line.startswith("#")
            or "=" not in line
        ):
            continue

        key, value = line.split(
            "=",
            1,
        )

        value = value.strip()

        if (
            len(value) >= 2
            and value[0] == value[-1]
            and value[0] in {"'", '"'}
        ):
            value = value[1:-1]

        values[key.strip()] = value

    return values


def require(
    values: dict[str, str],
    key: str,
) -> str:
    value = values.get(key)

    if (
        value is None
        or not value.strip()
    ):
        raise RuntimeError(
            f"Missing .env setting: {key}"
        )

    return value.strip()


async def main() -> None:
    environment = load_env(
        ENV_PATH
    )

    connection = await asyncpg.connect(
        host=require(
            environment,
            "POSTGRES_HOST",
        ),
        port=int(
            require(
                environment,
                "POSTGRES_PORT",
            )
        ),
        user=require(
            environment,
            "POSTGRES_USER",
        ),
        password=require(
            environment,
            "POSTGRES_PASSWORD",
        ),
        database=DATABASE_NAME,
    )

    try:
        rows = await connection.fetch(
            """
            SELECT
                id,
                device_id,
                process_name,
                status,
                started_at,
                ended_at,
                last_observed_at,
                duration_seconds
            FROM app_usage_intervals
            ORDER BY started_at DESC
            LIMIT 10
            """
        )

        if len(rows) < 2:
            raise RuntimeError(
                "At least two app usage intervals are required. "
                "Switch between two applications first."
            )

        newest = rows[0]

        previous = next(
            (
                row
                for row in rows[1:]
                if row["device_id"]
                == newest["device_id"]
                and row["process_name"].casefold()
                != newest["process_name"].casefold()
            ),
            None,
        )

        if previous is None:
            raise RuntimeError(
                "No recent application switch found for latest device."
            )

        if previous["status"] != "closed":
            raise RuntimeError(
                "Previous application interval is not closed."
            )

        if newest["status"] != "open":
            raise RuntimeError(
                "Newest application interval is not open."
            )

        if previous["duration_seconds"] < 0:
            raise RuntimeError(
                "Previous duration is negative."
            )

        if newest["duration_seconds"] < 0:
            raise RuntimeError(
                "Newest duration is negative."
            )

        now = datetime.now(
            timezone.utc
        )

        age_seconds = (
            now
            - newest["last_observed_at"]
        ).total_seconds()

        if age_seconds > MAXIMUM_AGE_SECONDS:
            raise RuntimeError(
                "Latest app interval is stale. "
                f"Age={age_seconds:.1f}s."
            )

        print(
            "PASS recent application switch found."
        )

        print(
            "Previous process:",
            previous["process_name"],
        )

        print(
            "Previous status:",
            previous["status"],
        )

        print(
            "Previous duration seconds:",
            previous["duration_seconds"],
        )

        print(
            "Current process:",
            newest["process_name"],
        )

        print(
            "Current status:",
            newest["status"],
        )

        print(
            "Current duration seconds:",
            newest["duration_seconds"],
        )

        print(
            "Latest age seconds:",
            round(
                age_seconds,
                1,
            ),
        )

    finally:
        await connection.close()


if __name__ == "__main__":
    asyncio.run(
        main()
    )
'@

$Runner =
    $Runner.Replace(
        "__ENV_PATH__",
        $EnvironmentFile.Replace(
            "\",
            "\\"
        )
    )

$Runner =
    $Runner.Replace(
        "__DATABASE_NAME__",
        $TenantDatabaseName
    )

$Runner =
    $Runner.Replace(
        "__MAXIMUM_AGE_SECONDS__",
        "$MaximumAgeSeconds"
    )

$Runner |
    & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw (
        "Phase 10 app-switch verification failed."
    )
}

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 10 APP SWITCH: PASS"
Write-Host "================================================="
Write-Host ""