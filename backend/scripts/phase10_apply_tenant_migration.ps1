#Requires -Version 5.1

param(
    [string]$TenantDatabaseName =
        "tenant_34527ffbe0944e5e89ee4cab97244fc3"
)

$ErrorActionPreference = "Stop"

$BackendRoot = "C:\workforce-os\backend"
$Python = "C:\workforce-os\.venv\Scripts\python.exe"
$EnvironmentFile = "C:\workforce-os\.env"

$MigrationFile =
    Join-Path `
        $BackendRoot `
        "migrations\tenant\versions\b1c2d3e4f5a6_add_app_tracking.py"

$ExpectedRevision = "a9b2c4d6e7f8"
$TargetRevision = "b1c2d3e4f5a6"

Write-Host ""
Write-Host "================================================="
Write-Host " WorkforceOS Phase 10 Tenant Migration"
Write-Host "================================================="
Write-Host ""
Write-Host "Tenant DB: $TenantDatabaseName"
Write-Host ""

if (-not (Test-Path $Python))
{
    throw "Python not found: $Python"
}

if (-not (Test-Path $EnvironmentFile))
{
    throw ".env not found: $EnvironmentFile"
}

if (-not (Test-Path $MigrationFile))
{
    throw "Migration not found: $MigrationFile"
}

Push-Location $BackendRoot

try
{
    Write-Host "[1/5] Compiling migration..."

    & $Python `
        -m py_compile `
        $MigrationFile

    if ($LASTEXITCODE -ne 0)
    {
        throw "Phase 10 migration compile failed."
    }

    Write-Host "PASS migration compile"
    Write-Host ""

    $Runner = @'
from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import inspect, text
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import create_async_engine


ENV_PATH = Path(r"__ENV_PATH__")
MIGRATION_PATH = Path(r"__MIGRATION_PATH__")

DATABASE_NAME = "__DATABASE_NAME__"
EXPECTED_REVISION = "__EXPECTED_REVISION__"
TARGET_REVISION = "__TARGET_REVISION__"


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

        value = value.strip()

        if (
            len(value) >= 2
            and value[0] == value[-1]
            and value[0] in {'"', "'"}
        ):
            value = value[1:-1]

        values[key.strip()] = value

    return values


def require(
    values: dict[str, str],
    key: str,
) -> str:
    value = values.get(key)

    if value is None or not value.strip():
        raise RuntimeError(
            f"Missing .env value: {key}"
        )

    return value.strip()


def load_migration():
    specification = importlib.util.spec_from_file_location(
        "phase10_app_tracking_migration",
        MIGRATION_PATH,
    )

    if (
        specification is None
        or specification.loader is None
    ):
        raise RuntimeError(
            "Unable to load Phase 10 migration."
        )

    module = importlib.util.module_from_spec(
        specification
    )

    specification.loader.exec_module(
        module
    )

    if module.revision != TARGET_REVISION:
        raise RuntimeError(
            f"Unexpected migration revision: {module.revision}"
        )

    if module.down_revision != EXPECTED_REVISION:
        raise RuntimeError(
            f"Unexpected migration parent: {module.down_revision}"
        )

    return module


def current_revision(connection) -> str | None:
    inspector = inspect(
        connection
    )

    if (
        "alembic_version"
        not in inspector.get_table_names()
    ):
        return None

    return connection.execute(
        text(
            "SELECT version_num "
            "FROM alembic_version "
            "LIMIT 1"
        )
    ).scalar_one_or_none()


def apply_upgrade(
    connection,
    module,
) -> None:
    context = MigrationContext.configure(
        connection
    )

    operations = Operations(
        context
    )

    original_op = module.op

    try:
        module.op = operations
        module.upgrade()
    finally:
        module.op = original_op


def set_revision(
    connection,
    revision: str,
) -> None:
    connection.execute(
        text(
            "UPDATE alembic_version "
            "SET version_num = :revision"
        ),
        {
            "revision": revision,
        },
    )


def verify_schema(connection) -> None:
    inspector = inspect(
        connection
    )

    tables = set(
        inspector.get_table_names()
    )

    required_tables = {
        "app_observations",
        "app_usage_intervals",
    }

    missing_tables = (
        required_tables
        - tables
    )

    if missing_tables:
        raise RuntimeError(
            "Missing Phase 10 tables: "
            + ", ".join(
                sorted(
                    missing_tables
                )
            )
        )

    observation_columns = {
        column["name"]
        for column
        in inspector.get_columns(
            "app_observations"
        )
    }

    required_observation_columns = {
        "id",
        "device_id",
        "employee_id",
        "app_key",
        "process_name",
        "executable_path",
        "window_title",
        "observed_at",
        "received_at",
        "created_at",
    }

    missing = (
        required_observation_columns
        - observation_columns
    )

    if missing:
        raise RuntimeError(
            "Missing app_observations columns: "
            + ", ".join(
                sorted(
                    missing
                )
            )
        )

    interval_columns = {
        column["name"]
        for column
        in inspector.get_columns(
            "app_usage_intervals"
        )
    }

    required_interval_columns = {
        "id",
        "device_id",
        "employee_id",
        "app_key",
        "process_name",
        "executable_path",
        "last_window_title",
        "status",
        "started_at",
        "ended_at",
        "last_observed_at",
        "duration_seconds",
        "created_at",
        "updated_at",
    }

    missing = (
        required_interval_columns
        - interval_columns
    )

    if missing:
        raise RuntimeError(
            "Missing app_usage_intervals columns: "
            + ", ".join(
                sorted(
                    missing
                )
            )
        )

    indexes = {
        item["name"]
        for item
        in inspector.get_indexes(
            "app_usage_intervals"
        )
    }

    if (
        "uq_app_usage_one_open_per_device"
        not in indexes
    ):
        raise RuntimeError(
            "Open app interval uniqueness index missing."
        )


def run_sync(
    connection,
    module,
) -> None:
    revision = current_revision(
        connection
    )

    print(
        "Current tenant revision:",
        revision,
    )

    if revision == TARGET_REVISION:
        print(
            "Phase 10 migration already applied."
        )

    elif revision == EXPECTED_REVISION:
        apply_upgrade(
            connection,
            module,
        )

        set_revision(
            connection,
            TARGET_REVISION,
        )

        print(
            "Phase 10 migration applied."
        )

    else:
        raise RuntimeError(
            "Unexpected tenant migration revision. "
            f"Expected {EXPECTED_REVISION} "
            f"or {TARGET_REVISION}; "
            f"received {revision!r}."
        )

    verify_schema(
        connection
    )

    final_revision = current_revision(
        connection
    )

    if final_revision != TARGET_REVISION:
        raise RuntimeError(
            "Final revision mismatch. "
            f"Expected {TARGET_REVISION}; "
            f"received {final_revision!r}."
        )

    print(
        "Final tenant revision:",
        final_revision,
    )

    print(
        "PASS app_observations table."
    )

    print(
        "PASS app_usage_intervals table."
    )

    print(
        "PASS required schema/indexes."
    )


async def main() -> None:
    environment = load_env(
        ENV_PATH
    )

    database_url = URL.create(
        drivername="postgresql+asyncpg",
        username=require(
            environment,
            "POSTGRES_USER",
        ),
        password=require(
            environment,
            "POSTGRES_PASSWORD",
        ),
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
        database=DATABASE_NAME,
    )

    engine = create_async_engine(
        database_url,
        pool_pre_ping=True,
    )

    try:
        module = load_migration()

        async with engine.begin() as connection:
            await connection.run_sync(
                run_sync,
                module,
            )
    finally:
        await engine.dispose()


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
            "__MIGRATION_PATH__",
            $MigrationFile.Replace(
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
            "__EXPECTED_REVISION__",
            $ExpectedRevision
        )

    $Runner =
        $Runner.Replace(
            "__TARGET_REVISION__",
            $TargetRevision
        )

    $Runner |
        & $Python -

    if ($LASTEXITCODE -ne 0)
    {
        throw "Phase 10 tenant migration failed."
    }

    Write-Host ""
    Write-Host "================================================="
    Write-Host " PHASE 10 TENANT MIGRATION: PASS"
    Write-Host "================================================="
    Write-Host ""
}
finally
{
    Pop-Location
}