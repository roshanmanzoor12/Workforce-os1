#Requires -Version 5.1

param(
    [string]$TenantDatabaseName =
        "tenant_34527ffbe0944e5e89ee4cab97244fc3"
)

$ErrorActionPreference =
    "Stop"

$Python =
    "C:\workforce-os\.venv\Scripts\python.exe"

$EnvironmentFile =
    "C:\workforce-os\.env"

$Runner = @'
from __future__ import annotations

import asyncio
from pathlib import Path

import asyncpg


ENV_PATH = Path(r"__ENV_PATH__")
DATABASE_NAME = "__DATABASE_NAME__"


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}

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

        values[
            key.strip()
        ] = value

    return values


def require(
    values: dict[str, str],
    key: str,
) -> str:
    value = values.get(
        key
    )

    if not value:
        raise RuntimeError(
            f"Missing .env value: {key}"
        )

    return value


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
                duration_seconds
            FROM app_usage_intervals
            ORDER BY started_at DESC
            LIMIT 20
            """
        )

        if len(rows) < 3:
            raise RuntimeError(
                "Need at least three recent app intervals."
            )

        latest_device = rows[0][
            "device_id"
        ]

        device_rows = [
            row
            for row in rows
            if row["device_id"]
            == latest_device
        ]

        if len(device_rows) < 3:
            raise RuntimeError(
                "Need at least three recent intervals for the same device."
            )

        newest = device_rows[0]
        middle = device_rows[1]
        oldest = device_rows[2]

        if (
            newest["process_name"].casefold()
            == middle["process_name"].casefold()
        ):
            raise RuntimeError(
                "Newest two intervals are not an app switch."
            )

        if (
            middle["process_name"].casefold()
            == oldest["process_name"].casefold()
        ):
            raise RuntimeError(
                "Previous two intervals are not an app switch."
            )

        if middle["status"] != "closed":
            raise RuntimeError(
                "Middle app interval must be closed."
            )

        if oldest["status"] != "closed":
            raise RuntimeError(
                "Oldest app interval must be closed."
            )

        if newest["status"] != "open":
            raise RuntimeError(
                "Newest app interval must be open."
            )

        print(
            "PASS three-stage app switch sequence."
        )

        print(
            "Oldest:",
            oldest["process_name"],
            oldest["duration_seconds"],
        )

        print(
            "Middle:",
            middle["process_name"],
            middle["duration_seconds"],
        )

        print(
            "Current:",
            newest["process_name"],
            newest["duration_seconds"],
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

$Runner |
    & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw (
        "Phase 10 switch-sequence verification failed."
    )
}

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 10 SWITCH SEQUENCE: PASS"
Write-Host "================================================="
Write-Host ""