#Requires -Version 5.1

param(
    [string]$TenantDatabaseName =
        "tenant_34527ffbe0944e5e89ee4cab97244fc3",

    [int]$SampleDelaySeconds =
        35
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
SAMPLE_DELAY_SECONDS = __SAMPLE_DELAY_SECONDS__


def load_env(
    path: Path,
) -> dict[str, str]:
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

    if (
        value is None
        or not value.strip()
    ):
        raise RuntimeError(
            f"Missing .env setting: {key}"
        )

    return value.strip()


async def latest_open(
    connection,
):
    return await connection.fetchrow(
        """
        SELECT
            id,
            device_id,
            process_name,
            status,
            last_observed_at,
            duration_seconds
        FROM app_usage_intervals
        WHERE status = 'open'
        ORDER BY last_observed_at DESC
        LIMIT 1
        """
    )


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
        before = await latest_open(
            connection
        )

        if before is None:
            raise RuntimeError(
                "No open app interval found."
            )

        print(
            "Initial process:",
            before["process_name"],
        )

        print(
            "Initial duration:",
            before["duration_seconds"],
        )

        print(
            f"Waiting {SAMPLE_DELAY_SECONDS} seconds..."
        )

        await asyncio.sleep(
            SAMPLE_DELAY_SECONDS
        )

        after = await latest_open(
            connection
        )

        if after is None:
            raise RuntimeError(
                "No open app interval found after wait."
            )

        if (
            after["id"]
            == before["id"]
        ):
            if (
                after["duration_seconds"]
                <= before["duration_seconds"]
            ):
                raise RuntimeError(
                    "Current app interval did not accumulate duration."
                )

            print(
                "PASS same foreground application accumulated duration."
            )

        else:
            print(
                "INFO foreground application changed during sample."
            )

            print(
                "Previous interval:",
                before["id"],
            )

            print(
                "New interval:",
                after["id"],
            )

        print(
            "Current process:",
            after["process_name"],
        )

        print(
            "Current duration:",
            after["duration_seconds"],
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
        "__SAMPLE_DELAY_SECONDS__",
        "$SampleDelaySeconds"
    )

$Runner |
    & $Python -

if ($LASTEXITCODE -ne 0)
{
    throw (
        "Phase 10 interval progression failed."
    )
}

Write-Host ""
Write-Host "================================================="
Write-Host " PHASE 10 INTERVAL PROGRESSION: PASS"
Write-Host "================================================="
Write-Host ""