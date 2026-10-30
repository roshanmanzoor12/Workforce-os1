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

Write-Host ""
Write-Host "================================================="
Write-Host " WorkforceOS Phase 09 Live Accumulation Check"
Write-Host "================================================="
Write-Host ""

$Runner = @'
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path

import asyncpg


ENV_PATH = Path(r"__ENV_PATH__")
TENANT_DATABASE_NAME = "__TENANT_DATABASE_NAME__"
MAXIMUM_AGE_SECONDS = __MAXIMUM_AGE_SECONDS__


def load_env(path: Path) -> dict[str, str]:
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

        key = key.strip()
        value = value.strip()

        if (
            len(value) >= 2
            and value[0] == value[-1]
            and value[0] in {'"', "'"}
        ):
            value = value[1:-1]

        values[key] = value

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
        database=TENANT_DATABASE_NAME,
    )

    try:
        activity = await connection.fetchrow(
            """
            SELECT
                id,
                device_id,
                employee_id,
                state,
                idle_seconds,
                observed_at,
                received_at
            FROM activity_state_events
            ORDER BY observed_at DESC
            LIMIT 1
            """
        )

        if activity is None:
            raise RuntimeError(
                "No activity event found."
            )

        work_session = await connection.fetchrow(
            """
            SELECT
                id,
                device_id,
                employee_id,
                status,
                current_state,
                started_at,
                ended_at,
                last_observed_at,
                active_seconds,
                idle_seconds
            FROM work_sessions
            WHERE device_id = $1
            ORDER BY last_observed_at DESC
            LIMIT 1
            """,
            activity["device_id"],
        )

        if work_session is None:
            raise RuntimeError(
                "No work session found for latest activity device."
            )

        if (
            work_session["last_observed_at"]
            != activity["observed_at"]
        ):
            raise RuntimeError(
                "Latest work session has not consumed the latest "
                "activity observation. "
                f"Activity={activity['observed_at']!s}, "
                f"Session={work_session['last_observed_at']!s}."
            )

        if (
            work_session["current_state"]
            != activity["state"]
        ):
            raise RuntimeError(
                "Work session state does not match latest activity state. "
                f"Activity={activity['state']!r}, "
                f"Session={work_session['current_state']!r}."
            )

        active_seconds = (
            work_session[
                "active_seconds"
            ]
        )

        idle_seconds = (
            work_session[
                "idle_seconds"
            ]
        )

        if active_seconds < 0:
            raise RuntimeError(
                "active_seconds cannot be negative."
            )

        if idle_seconds < 0:
            raise RuntimeError(
                "idle_seconds cannot be negative."
            )

        now = datetime.now(
            timezone.utc
        )

        age_seconds = (
            now
            - work_session[
                "last_observed_at"
            ]
        ).total_seconds()

        if age_seconds > MAXIMUM_AGE_SECONDS:
            raise RuntimeError(
                "Latest work session is stale. "
                f"Age={age_seconds:.1f}s."
            )

        print(
            "PASS latest activity event consumed by work session."
        )

        print(
            "Activity Event ID:",
            activity["id"],
        )

        print(
            "Work Session ID:",
            work_session["id"],
        )

        print(
            "Device ID:",
            work_session["device_id"],
        )

        print(
            "Employee ID:",
            work_session["employee_id"],
        )

        print(
            "Status:",
            work_session["status"],
        )

        print(
            "Current state:",
            work_session["current_state"],
        )

        print(
            "Started at:",
            work_session["started_at"],
        )

        print(
            "Last observed at:",
            work_session["last_observed_at"],
        )

        print(
            "Active seconds:",
            active_seconds,
        )

        print(
            "Idle seconds:",
            idle_seconds,
        )

        print(
            "Total seconds:",
            active_seconds + idle_seconds,
        )

        print(
            "Event age seconds:",
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
        "__TENANT_DATABASE_NAME__",
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
        "Phase 09 live accumulation verification failed."
    )
}

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 09 LIVE ACCUMULATION: PASS"
Write-Host "================================================="
Write-Host ""