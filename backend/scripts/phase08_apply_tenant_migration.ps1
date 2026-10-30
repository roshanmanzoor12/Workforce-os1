#Requires -Version 5.1

param(
    [string]$TenantDatabaseName =
        "tenant_34527ffbe0944e5e89ee4cab97244fc3"
)

$ErrorActionPreference = "Stop"

$BackendDirectory = "C:\workforce-os\backend"
$Python = "C:\workforce-os\.venv\Scripts\python.exe"
$EnvironmentFile = "C:\workforce-os\.env"

$MigrationFile = Join-Path `
    $BackendDirectory `
    "migrations\tenant\versions\f8a1c3d4e5b6_add_activity_state_events.py"

$ExpectedCurrentRevision = "c5e4d7a91b26"
$TargetRevision = "f8a1c3d4e5b6"

Write-Host ""
Write-Host "================================================="
Write-Host " WorkforceOS Phase 08 Tenant Migration"
Write-Host "================================================="
Write-Host ""
Write-Host "Tenant DB: $TenantDatabaseName"
Write-Host ""

if (-not (Test-Path $Python))
{
    throw "WorkforceOS Python not found: $Python"
}

if (-not (Test-Path $EnvironmentFile))
{
    throw "WorkforceOS .env not found: $EnvironmentFile"
}

if (-not (Test-Path $MigrationFile))
{
    throw "Phase 08 migration file not found: $MigrationFile"
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
        throw "Phase 08 migration compile failed."
    }

    Write-Host "PASS migration compile"
    Write-Host ""

    Write-Host "[2/5] Loading PostgreSQL configuration..."
    Write-Host "[3/5] Checking tenant revision..."
    Write-Host "[4/5] Applying migration if required..."
    Write-Host "[5/5] Verifying schema..."
    Write-Host ""

    $Runner = @'
from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.engine import URL


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


def require_env(
    values: dict[str, str],
    key: str,
) -> str:
    value = values.get(key)

    if (
        value is None
        or not value.strip()
    ):
        raise RuntimeError(
            f"Required environment value missing: {key}"
        )

    return value.strip()


def build_tenant_url(
    values: dict[str, str],
) -> URL:
    host = require_env(
        values,
        "POSTGRES_HOST",
    )

    port = int(
        require_env(
            values,
            "POSTGRES_PORT",
        )
    )

    user = require_env(
        values,
        "POSTGRES_USER",
    )

    password = require_env(
        values,
        "POSTGRES_PASSWORD",
    )

    return URL.create(
        drivername="postgresql+asyncpg",
        username=user,
        password=password,
        host=host,
        port=port,
        database=TENANT_DATABASE_NAME,
    )


def load_migration():
    spec = importlib.util.spec_from_file_location(
        "phase08_activity_migration",
        MIGRATION_PATH,
    )

    if (
        spec is None
        or spec.loader is None
    ):
        raise RuntimeError(
            "Unable to load Phase 08 migration file."
        )

    module = importlib.util.module_from_spec(
        spec
    )

    spec.loader.exec_module(
        module
    )

    if module.revision != TARGET_REVISION:
        raise RuntimeError(
            f"Unexpected migration revision: {module.revision}"
        )

    if module.down_revision != EXPECTED_CURRENT_REVISION:
        raise RuntimeError(
            f"Unexpected migration parent: {module.down_revision}"
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


def set_revision(
    connection,
    revision: str,
) -> None:
    current = get_revision(
        connection
    )

    if current is None:
        connection.execute(
            text(
                "INSERT INTO alembic_version "
                "(version_num) "
                "VALUES (:revision)"
            ),
            {
                "revision": revision,
            },
        )
    else:
        connection.execute(
            text(
                "UPDATE alembic_version "
                "SET version_num = :revision"
            ),
            {
                "revision": revision,
            },
        )


def apply_upgrade(
    connection,
    migration_module,
) -> None:
    context = MigrationContext.configure(
        connection
    )

    operations = Operations(
        context
    )

    original_op = migration_module.op

    try:
        migration_module.op = operations
        migration_module.upgrade()
    finally:
        migration_module.op = original_op


def verify_schema(
    connection,
) -> None:
    inspector = inspect(
        connection
    )

    tables = set(
        inspector.get_table_names()
    )

    if (
        "activity_state_events"
        not in tables
    ):
        raise RuntimeError(
            "activity_state_events table was not created."
        )

    columns = {
        column["name"]
        for column
        in inspector.get_columns(
            "activity_state_events"
        )
    }

    required_columns = {
        "id",
        "device_id",
        "employee_id",
        "state",
        "idle_seconds",
        "last_input_at",
        "observed_at",
        "received_at",
        "created_at",
    }

    missing_columns = (
        required_columns
        - columns
    )

    if missing_columns:
        raise RuntimeError(
            "Missing activity_state_events columns: "
            + ", ".join(
                sorted(
                    missing_columns
                )
            )
        )

    indexes = {
        index["name"]
        for index
        in inspector.get_indexes(
            "activity_state_events"
        )
    }

    required_indexes = {
        "ix_activity_state_events_device_observed_at",
        "ix_activity_state_events_employee_observed_at",
        "ix_activity_state_events_received_at",
    }

    missing_indexes = (
        required_indexes
        - indexes
    )

    if missing_indexes:
        raise RuntimeError(
            "Missing activity indexes: "
            + ", ".join(
                sorted(
                    missing_indexes
                )
            )
        )


def migrate_sync(
    connection,
    migration_module,
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
            "Phase 08 migration already applied."
        )

    elif current_revision == EXPECTED_CURRENT_REVISION:
        apply_upgrade(
            connection,
            migration_module,
        )

        set_revision(
            connection,
            TARGET_REVISION,
        )

        print(
            "Phase 08 migration applied."
        )

    else:
        raise RuntimeError(
            "Unexpected tenant migration revision. "
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
            "Final tenant migration revision mismatch. "
            f"Expected {TARGET_REVISION}, "
            f"received {final_revision!r}."
        )

    print(
        "Final tenant revision:",
        final_revision,
    )

    print(
        "PASS activity_state_events table exists."
    )

    print(
        "PASS required columns exist."
    )

    print(
        "PASS required indexes exist."
    )


async def main() -> None:
    env = load_env(
        ENV_PATH
    )

    database_url = build_tenant_url(
        env
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
        "Resolved PostgreSQL user:",
        database_url.username,
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
        migration_module = (
            load_migration()
        )

        async with engine.begin() as connection:
            await connection.run_sync(
                migrate_sync,
                migration_module,
            )
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(
        main()
    )
'@

    $Runner = $Runner.Replace(
        "__ENV_PATH__",
        $EnvironmentFile.Replace(
            "\",
            "\\"
        )
    )

    $Runner = $Runner.Replace(
        "__MIGRATION_PATH__",
        $MigrationFile.Replace(
            "\",
            "\\"
        )
    )

    $Runner = $Runner.Replace(
        "__TENANT_DATABASE_NAME__",
        $TenantDatabaseName
    )

    $Runner = $Runner.Replace(
        "__EXPECTED_CURRENT_REVISION__",
        $ExpectedCurrentRevision
    )

    $Runner = $Runner.Replace(
        "__TARGET_REVISION__",
        $TargetRevision
    )

    $Runner |
        & $Python -

    if ($LASTEXITCODE -ne 0)
    {
        throw "Phase 08 tenant migration failed."
    }

    Write-Host ""
    Write-Host "================================================="
    Write-Host " PHASE 08 TENANT MIGRATION: PASS"
    Write-Host "================================================="
    Write-Host ""
}
finally
{
    Pop-Location
}