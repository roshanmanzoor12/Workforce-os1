#Requires -Version 5.1

param(
    [string]$TenantDatabaseName =
        "tenant_34527ffbe0944e5e89ee4cab97244fc3"
)

$ErrorActionPreference = "Stop"

$BackendDirectory = "C:\workforce-os\backend"
$Python = "C:\workforce-os\.venv\Scripts\python.exe"
$EnvironmentFile = "C:\workforce-os\.env"

$MigrationFile =
    Join-Path `
        $BackendDirectory `
        "migrations\tenant\versions\a9b2c4d6e7f8_add_work_sessions.py"

$ExpectedCurrentRevision =
    "f8a1c3d4e5b6"

$TargetRevision =
    "a9b2c4d6e7f8"

Write-Host ""
Write-Host "================================================="
Write-Host " WorkforceOS Phase 09 Tenant Migration"
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
    throw "Phase 09 migration not found: $MigrationFile"
}

Push-Location $BackendDirectory

try
{
    Write-Host "[1/5] Compiling migration..."

    & $Python `
        -m py_compile `
        $MigrationFile

    if ($LASTEXITCODE -ne 0)
    {
        throw "Phase 09 migration compile failed."
    }

    Write-Host "PASS migration compile"
    Write-Host ""

    Write-Host "[2/5] Loading PostgreSQL configuration..."
    Write-Host "[3/5] Checking tenant revision..."
    Write-Host "[4/5] Applying migration if required..."
    Write-Host "[5/5] Verifying work_sessions schema..."
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

TENANT_DATABASE_NAME = "__TENANT_DATABASE_NAME__"
EXPECTED_CURRENT_REVISION = "__EXPECTED_CURRENT_REVISION__"
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
    value = values.get(key)

    if (
        value is None
        or not value.strip()
    ):
        raise RuntimeError(
            f"Missing required environment value: {key}"
        )

    return value.strip()


def build_url(
    values: dict[str, str],
) -> URL:
    return URL.create(
        drivername="postgresql+asyncpg",
        username=require_value(
            values,
            "POSTGRES_USER",
        ),
        password=require_value(
            values,
            "POSTGRES_PASSWORD",
        ),
        host=require_value(
            values,
            "POSTGRES_HOST",
        ),
        port=int(
            require_value(
                values,
                "POSTGRES_PORT",
            )
        ),
        database=TENANT_DATABASE_NAME,
    )


def load_migration():
    spec = importlib.util.spec_from_file_location(
        "phase09_work_sessions_migration",
        MIGRATION_PATH,
    )

    if (
        spec is None
        or spec.loader is None
    ):
        raise RuntimeError(
            "Unable to load Phase 09 migration."
        )

    module = importlib.util.module_from_spec(
        spec
    )

    spec.loader.exec_module(
        module
    )

    if module.revision != TARGET_REVISION:
        raise RuntimeError(
            f"Unexpected revision: {module.revision}"
        )

    if module.down_revision != EXPECTED_CURRENT_REVISION:
        raise RuntimeError(
            f"Unexpected parent revision: {module.down_revision}"
        )

    return module


def get_revision(
    connection,
) -> str | None:
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


def verify_schema(
    connection,
) -> None:
    inspector = inspect(
        connection
    )

    if (
        "work_sessions"
        not in inspector.get_table_names()
    ):
        raise RuntimeError(
            "work_sessions table does not exist."
        )

    columns = {
        column["name"]
        for column
        in inspector.get_columns(
            "work_sessions"
        )
    }

    required_columns = {
        "id",
        "device_id",
        "employee_id",
        "status",
        "current_state",
        "started_at",
        "ended_at",
        "last_observed_at",
        "active_seconds",
        "idle_seconds",
        "created_at",
        "updated_at",
    }

    missing_columns = (
        required_columns
        - columns
    )

    if missing_columns:
        raise RuntimeError(
            "Missing work_sessions columns: "
            + ", ".join(
                sorted(
                    missing_columns
                )
            )
        )

    indexes = {
        item["name"]
        for item
        in inspector.get_indexes(
            "work_sessions"
        )
    }

    required_indexes = {
        "ix_work_sessions_device_started_at",
        "ix_work_sessions_employee_started_at",
        "ix_work_sessions_status_last_observed_at",
        "uq_work_sessions_one_open_per_device",
    }

    missing_indexes = (
        required_indexes
        - indexes
    )

    if missing_indexes:
        raise RuntimeError(
            "Missing work_sessions indexes: "
            + ", ".join(
                sorted(
                    missing_indexes
                )
            )
        )


def run_sync(
    connection,
    module,
) -> None:
    current_revision = get_revision(
        connection
    )

    print(
        "Current tenant revision:",
        current_revision,
    )

    if current_revision == TARGET_REVISION:
        print(
            "Phase 09 migration already applied."
        )

    elif current_revision == EXPECTED_CURRENT_REVISION:
        apply_upgrade(
            connection,
            module,
        )

        set_revision(
            connection,
            TARGET_REVISION,
        )

        print(
            "Phase 09 migration applied."
        )

    else:
        raise RuntimeError(
            "Unexpected tenant revision. "
            f"Expected {EXPECTED_CURRENT_REVISION} "
            f"or {TARGET_REVISION}; "
            f"received {current_revision!r}."
        )

    verify_schema(
        connection
    )

    final_revision = get_revision(
        connection
    )

    if final_revision != TARGET_REVISION:
        raise RuntimeError(
            "Final revision verification failed. "
            f"Expected {TARGET_REVISION}; "
            f"received {final_revision!r}."
        )

    print(
        "Final tenant revision:",
        final_revision,
    )

    print(
        "PASS work_sessions table exists."
    )

    print(
        "PASS required columns exist."
    )

    print(
        "PASS required indexes exist."
    )


async def main() -> None:
    environment = load_env(
        ENV_PATH
    )

    database_url = build_url(
        environment
    )

    print(
        "Resolved PostgreSQL host:",
        database_url.host,
    )

    print(
        "Resolved PostgreSQL port:",
        database_url.port,
    )

    print(
        "Resolved tenant database:",
        TENANT_DATABASE_NAME,
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
            "__TENANT_DATABASE_NAME__",
            $TenantDatabaseName
        )

    $Runner =
        $Runner.Replace(
            "__EXPECTED_CURRENT_REVISION__",
            $ExpectedCurrentRevision
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
        throw "Phase 09 tenant migration failed."
    }

    Write-Host ""
    Write-Host "================================================="
    Write-Host " PHASE 09 TENANT MIGRATION: PASS"
    Write-Host "================================================="
    Write-Host ""
}
finally
{
    Pop-Location
}