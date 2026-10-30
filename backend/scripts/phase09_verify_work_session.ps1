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
Write-Host " WorkforceOS Phase 09 Work Session Verification"
Write-Host "================================================="
Write-Host ""

if (-not (Test-Path $Python))
{
    throw "Python not found: $Python"
}

if (-not (Test-Path $EnvironmentFile))
{
    throw ".env not found: $EnvironmentFile"
}

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
            f"Missing environment value: {key}"
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
        table_exists = await connection.fetchval(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = 'work_sessions'
            )
            """
        )

        if not table_exists:
            raise RuntimeError(
                "work_sessions table does not exist."
            )

        row = await connection.fetchrow(
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
                idle_seconds,
                created_at,
                updated_at
            FROM work_sessions
            ORDER BY last_observed_at DESC
            LIMIT 1
            """
        )

        if row is None:
            raise RuntimeError(
                "No work_sessions rows found. "
                "Run live activity after enabling the Phase 09 hook."
            )

        if row["status"] not in {
            "open",
            "closed",
        }:
            raise RuntimeError(
                f"Unexpected status: {row['status']!r}"
            )

        if row["current_state"] not in {
            "active",
            "idle",
        }:
            raise RuntimeError(
                "Unexpected current_state: "
                f"{row['current_state']!r}"
            )

        active_seconds = row["active_seconds"]
        idle_seconds = row["idle_seconds"]

        if active_seconds < 0:
            raise RuntimeError(
                "active_seconds is negative."
            )

        if idle_seconds < 0:
            raise RuntimeError(
                "idle_seconds is negative."
            )

        last_observed_at = row[
            "last_observed_at"
        ]

        now = datetime.now(
            timezone.utc
        )

        age_seconds = (
            now
            - last_observed_at
        ).total_seconds()

        if age_seconds > MAXIMUM_AGE_SECONDS:
            raise RuntimeError(
                "Latest work session is stale. "
                f"Age={age_seconds:.1f}s, "
                f"maximum={MAXIMUM_AGE_SECONDS}s."
            )

        print(
            "PASS latest work session found."
        )

        print(
            "Session ID:",
            row["id"],
        )

        print(
            "Device ID:",
            row["device_id"],
        )

        print(
            "Employee ID:",
            row["employee_id"],
        )

        print(
            "Status:",
            row["status"],
        )

        print(
            "Current state:",
            row["current_state"],
        )

        print(
            "Started at:",
            row["started_at"],
        )

        print(
            "Ended at:",
            row["ended_at"],
        )

        print(
            "Last observed at:",
            last_observed_at,
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
            "Age seconds:",
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
        "Phase 09 live work-session verification failed."
    )
}

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 09 WORK SESSION VERIFICATION: PASS"
Write-Host "================================================="
Write-Host ""