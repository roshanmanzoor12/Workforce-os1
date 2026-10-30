#Requires -Version 5.1

param(
    [string]$TenantDatabaseName =
        "tenant_34527ffbe0944e5e89ee4cab97244fc3",

    [int]$MaximumAgeSeconds =
        180
)

$ErrorActionPreference = "Stop"

$BackendDirectory =
    "C:\workforce-os\backend"

$Python =
    "C:\workforce-os\.venv\Scripts\python.exe"

$EnvironmentFile =
    "C:\workforce-os\.env"

Write-Host ""
Write-Host "================================================="
Write-Host " WorkforceOS Phase 08 Activity Event Verification"
Write-Host "================================================="
Write-Host ""

if (-not (Test-Path $Python))
{
    throw (
        "WorkforceOS Python not found: " +
        $Python
    )
}

if (-not (Test-Path $EnvironmentFile))
{
    throw (
        "WorkforceOS .env not found: " +
        $EnvironmentFile
    )
}

Push-Location $BackendDirectory

try
{
    Write-Host "[1/4] Loading PostgreSQL configuration..."
    Write-Host "[2/4] Connecting to tenant database..."
    Write-Host "[3/4] Reading latest activity event..."
    Write-Host "[4/4] Verifying event freshness and state..."
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


def require_value(
    values: dict[str, str],
    key: str,
) -> str:
    value = values.get(
        key
    )

    if (
        value is None
        or not value.strip()
    ):
        raise RuntimeError(
            f"Missing required environment value: {key}"
        )

    return value.strip()


async def main() -> None:
    env = load_env(
        ENV_PATH
    )

    host = require_value(
        env,
        "POSTGRES_HOST",
    )

    port = int(
        require_value(
            env,
            "POSTGRES_PORT",
        )
    )

    user = require_value(
        env,
        "POSTGRES_USER",
    )

    password = require_value(
        env,
        "POSTGRES_PASSWORD",
    )

    connection = await asyncpg.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=TENANT_DATABASE_NAME,
    )

    try:
        table_exists = await connection.fetchval(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = 'activity_state_events'
            )
            """
        )

        if not table_exists:
            raise RuntimeError(
                "activity_state_events table does not exist."
            )

        row = await connection.fetchrow(
            """
            SELECT
                id,
                device_id,
                employee_id,
                state,
                idle_seconds,
                last_input_at,
                observed_at,
                received_at,
                created_at
            FROM activity_state_events
            ORDER BY received_at DESC
            LIMIT 1
            """
        )

        if row is None:
            raise RuntimeError(
                "No activity_state_events rows found. "
                "Run the interactive activity helper before verification."
            )

        state = row["state"]

        if state not in {
            "active",
            "idle",
        }:
            raise RuntimeError(
                f"Unexpected activity state: {state!r}"
            )

        idle_seconds = row["idle_seconds"]

        if (
            idle_seconds is None
            or idle_seconds < 0
        ):
            raise RuntimeError(
                "Latest activity event has invalid idle_seconds."
            )

        received_at = row["received_at"]

        if received_at is None:
            raise RuntimeError(
                "Latest activity event has no received_at timestamp."
            )

        now = datetime.now(
            timezone.utc
        )

        age_seconds = (
            now
            - received_at
        ).total_seconds()

        if age_seconds < -120:
            raise RuntimeError(
                "Latest activity event timestamp is too far in the future."
            )

        if age_seconds > MAXIMUM_AGE_SECONDS:
            raise RuntimeError(
                "Latest activity event is stale. "
                f"Age={age_seconds:.1f}s, "
                f"maximum={MAXIMUM_AGE_SECONDS}s."
            )

        print(
            "PASS latest activity event found."
        )

        print(
            "Event ID:",
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
            "State:",
            state,
        )

        print(
            "Idle seconds:",
            idle_seconds,
        )

        print(
            "Observed at:",
            row["observed_at"],
        )

        print(
            "Received at:",
            received_at,
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
            "Phase 08 activity event verification failed."
        )
    }

    Write-Host ""
    Write-Host "================================================="
    Write-Host " PHASE 08 ACTIVITY EVENT VERIFICATION: PASS"
    Write-Host "================================================="
    Write-Host ""
}
finally
{
    Pop-Location
}