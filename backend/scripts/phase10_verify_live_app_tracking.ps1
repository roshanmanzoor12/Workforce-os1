#Requires -Version 5.1

param(
    [string]$TenantDatabaseName =
        "tenant_34527ffbe0944e5e89ee4cab97244fc3",

    [int]$MaximumAgeSeconds =
        180
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


def load_env(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}

    for raw in path.read_text(
        encoding="utf-8-sig"
    ).splitlines():
        line = raw.strip()

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

        result[key.strip()] = value

    return result


def require(
    values: dict[str, str],
    key: str,
) -> str:
    value = values.get(key)

    if not value:
        raise RuntimeError(
            f"Missing .env setting: {key}"
        )

    return value


async def main() -> None:
    env = load_env(
        ENV_PATH
    )

    connection = await asyncpg.connect(
        host=require(
            env,
            "POSTGRES_HOST",
        ),
        port=int(
            require(
                env,
                "POSTGRES_PORT",
            )
        ),
        user=require(
            env,
            "POSTGRES_USER",
        ),
        password=require(
            env,
            "POSTGRES_PASSWORD",
        ),
        database=DATABASE_NAME,
    )

    try:
        observation = await connection.fetchrow(
            """
            SELECT
                id,
                device_id,
                employee_id,
                app_key,
                process_name,
                executable_path,
                window_title,
                observed_at,
                received_at
            FROM app_observations
            ORDER BY observed_at DESC
            LIMIT 1
            """
        )

        if observation is None:
            raise RuntimeError(
                "No app observations found."
            )

        interval = await connection.fetchrow(
            """
            SELECT
                id,
                device_id,
                employee_id,
                app_key,
                process_name,
                status,
                started_at,
                ended_at,
                last_observed_at,
                duration_seconds
            FROM app_usage_intervals
            WHERE device_id = $1
            ORDER BY last_observed_at DESC
            LIMIT 1
            """,
            observation["device_id"],
        )

        if interval is None:
            raise RuntimeError(
                "No app usage interval found."
            )

        if (
            interval["app_key"]
            != observation["app_key"]
        ):
            raise RuntimeError(
                "Latest usage interval does not match latest observation."
            )

        now = datetime.now(
            timezone.utc
        )

        age = (
            now
            - observation["observed_at"]
        ).total_seconds()

        if age > MAXIMUM_AGE_SECONDS:
            raise RuntimeError(
                f"Latest app observation is stale. Age={age:.1f}s."
            )

        if observation["window_title"] is not None:
            raise RuntimeError(
                "Window title was stored even though title capture is disabled."
            )

        print(
            "PASS live application observation found."
        )

        print(
            "Observation ID:",
            observation["id"],
        )

        print(
            "Interval ID:",
            interval["id"],
        )

        print(
            "Device ID:",
            observation["device_id"],
        )

        print(
            "Process:",
            observation["process_name"],
        )

        print(
            "Executable:",
            observation["executable_path"],
        )

        print(
            "Window title:",
            observation["window_title"],
        )

        print(
            "Status:",
            interval["status"],
        )

        print(
            "Duration seconds:",
            interval["duration_seconds"],
        )

        print(
            "Observed at:",
            observation["observed_at"],
        )

        print(
            "Age seconds:",
            round(
                age,
                1,
            ),
        )

    finally:
        await connection.close()


if __name__ == "__main__":
    asyncio.run(main())
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
    throw "Phase 10 live App Tracking verification failed."
}

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 10 LIVE APP TRACKING: PASS"
Write-Host "================================================="