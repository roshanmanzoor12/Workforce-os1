#Requires -Version 5.1

param(
    [string]$TenantDatabaseName =
        "tenant_34527ffbe0944e5e89ee4cab97244fc3",

    [int]$LookbackMinutes =
        15
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
Write-Host " WorkforceOS Phase 08 Active/Idle Transition"
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
    Write-Host "[3/4] Reading recent activity states..."
    Write-Host "[4/4] Verifying active -> idle transition..."
    Write-Host ""

    $Runner = @'
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path

import asyncpg


ENV_PATH = Path(r"__ENV_PATH__")
TENANT_DATABASE_NAME = "__TENANT_DATABASE_NAME__"
LOOKBACK_MINUTES = __LOOKBACK_MINUTES__


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
        cutoff = (
            datetime.now(
                timezone.utc
            )
            - timedelta(
                minutes=LOOKBACK_MINUTES
            )
        )

        rows = await connection.fetch(
            """
            SELECT
                id,
                device_id,
                employee_id,
                state,
                idle_seconds,
                last_input_at,
                observed_at,
                received_at
            FROM activity_state_events
            WHERE received_at >= $1
            ORDER BY received_at ASC
            """,
            cutoff,
        )

        if not rows:
            raise RuntimeError(
                "No recent activity events found. "
                "Run the helper and generate active/idle activity first."
            )

        active_rows = [
            row
            for row in rows
            if row["state"] == "active"
        ]

        idle_rows = [
            row
            for row in rows
            if row["state"] == "idle"
        ]

        if not active_rows:
            raise RuntimeError(
                "No recent active event found."
            )

        if not idle_rows:
            raise RuntimeError(
                "No recent idle event found."
            )

        valid_transition = None

        for active in active_rows:
            for idle in idle_rows:
                if (
                    idle["device_id"]
                    == active["device_id"]
                    and idle["received_at"]
                    > active["received_at"]
                ):
                    valid_transition = (
                        active,
                        idle,
                    )
                    break

            if valid_transition is not None:
                break

        if valid_transition is None:
            raise RuntimeError(
                "Active and idle events exist, "
                "but no active -> idle transition "
                "for the same device was found."
            )

        active, idle = (
            valid_transition
        )

        if idle["idle_seconds"] <= 0:
            raise RuntimeError(
                "Idle event has invalid idle_seconds."
            )

        if (
            idle["observed_at"]
            <= active["observed_at"]
        ):
            raise RuntimeError(
                "Idle observation timestamp is not after active observation."
            )

        print(
            "PASS active event found."
        )

        print(
            "Active event ID:",
            active["id"],
        )

        print(
            "Active received at:",
            active["received_at"],
        )

        print(
            "Active idle seconds:",
            active["idle_seconds"],
        )

        print()

        print(
            "PASS idle event found."
        )

        print(
            "Idle event ID:",
            idle["id"],
        )

        print(
            "Idle received at:",
            idle["received_at"],
        )

        print(
            "Idle idle seconds:",
            idle["idle_seconds"],
        )

        print()

        transition_seconds = (
            idle["received_at"]
            - active["received_at"]
        ).total_seconds()

        print(
            "Transition seconds:",
            round(
                transition_seconds,
                1,
            ),
        )

        print(
            "PASS active -> idle transition verified."
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
            "__LOOKBACK_MINUTES__",
            "$LookbackMinutes"
        )

    $Runner |
        & $Python -

    if ($LASTEXITCODE -ne 0)
    {
        throw (
            "Phase 08 active/idle transition verification failed."
        )
    }

    Write-Host ""
    Write-Host "================================================="
    Write-Host " PHASE 08 ACTIVE -> IDLE TRANSITION: PASS"
    Write-Host "================================================="
    Write-Host ""
}
finally
{
    Pop-Location
}