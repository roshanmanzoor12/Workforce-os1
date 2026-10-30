from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import (
    Connection,
)
from sqlalchemy.ext.asyncio import (
    async_engine_from_config,
)


# =========================================================
# PROJECT IMPORT PATH
# =========================================================


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

project_root_str = str(
    PROJECT_ROOT
)

if (
    project_root_str
    not in sys.path
):
    sys.path.insert(
        0,
        project_root_str,
    )


# =========================================================
# APPLICATION IMPORTS
# =========================================================


from app.db.tenant import (  # noqa: E402
    build_tenant_database_url,
    validate_tenant_database_name,
)
from app.db.tenant_base import (  # noqa: E402
    TenantBase,
)

# ---------------------------------------------------------
# TENANT ORM REGISTRATION
# ---------------------------------------------------------
#
# Every tenant-local ORM module needed by the current tenant
# schema must be imported before target_metadata is inspected.
#
# These imports are intentionally unused directly; importing
# them registers their mapped tables with TenantBase.metadata.
# ---------------------------------------------------------

from app.db import tenant_models  # noqa: E402,F401

from app.modules.employees import (  # noqa: E402,F401
    models as employee_models,
)

from app.modules.devices import (  # noqa: E402,F401
    models as device_models,
)

from app.modules.devices import (  # noqa: E402,F401
    credential_models
    as device_credential_models,
)

from app.modules.shifts import (  # noqa: E402,F401
    models as shift_models,
)

from app.modules.holidays import (  # noqa: E402,F401
    models as holiday_models,
)

from app.modules.leave import (  # noqa: E402,F401
    models as leave_models,
)


from app.modules.payroll import models as payroll_models  # noqa: F401
from app.modules.payroll import payslip_models  # noqa: F401


# =========================================================
# ALEMBIC CONFIG
# =========================================================


config = context.config


# =========================================================
# TARGET METADATA
# =========================================================


target_metadata = (
    TenantBase.metadata
)


# =========================================================
# TENANT TARGET RESOLUTION
# =========================================================


def get_tenant_database_name() -> str:
    """
    Resolve the tenant database supplied by trusted backend/CLI
    infrastructure.

    Expected invocation:

        alembic \
            -c alembic.tenant.ini \
            -x database_name=tenant_<uuidhex> \
            upgrade head

    Security:

    - arbitrary database URLs are never accepted
    - database_name must pass the WorkforceOS validator
    - host/port/credentials come from trusted application config
    """

    arguments = (
        context.get_x_argument(
            as_dictionary=True
        )
    )

    database_name = (
        arguments.get(
            "database_name"
        )
    )

    if not database_name:
        raise RuntimeError(
            "Tenant migration requires "
            "-x database_name="
            "tenant_<workspace_uuid_hex>."
        )

    return (
        validate_tenant_database_name(
            database_name
        )
    )


def get_tenant_database_url() -> str:
    """
    Build the trusted SQLAlchemy URL for the selected tenant DB.

    The complete URL is never accepted from command-line input.
    """

    database_name = (
        get_tenant_database_name()
    )

    url = (
        build_tenant_database_url(
            database_name
        )
    )

    return url.render_as_string(
        hide_password=False
    )


# =========================================================
# OFFLINE MIGRATIONS
# =========================================================


def run_migrations_offline() -> None:
    """
    Run tenant migrations in SQL-generation mode.
    """

    url = (
        get_tenant_database_url()
    )

    context.configure(
        url=url,
        target_metadata=(
            target_metadata
        ),
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named",
        },
        compare_type=True,
        compare_server_default=True,
        include_schemas=False,
    )

    with context.begin_transaction():
        context.run_migrations()


# =========================================================
# MIGRATION CONFIGURATION
# =========================================================


def do_run_migrations(
    connection: Connection,
) -> None:
    """
    Configure Alembic against exactly one tenant PostgreSQL DB.
    """

    context.configure(
        connection=connection,
        target_metadata=(
            target_metadata
        ),
        compare_type=True,
        compare_server_default=True,
        include_schemas=False,
    )

    with context.begin_transaction():
        context.run_migrations()


# =========================================================
# ONLINE ASYNC MIGRATIONS
# =========================================================


async def run_async_migrations() -> None:
    """
    Run migrations against exactly one tenant database.
    """

    tenant_database_url = (
        get_tenant_database_url()
    )

    configuration = (
        config.get_section(
            config.config_ini_section,
            {},
        )
    )

    configuration[
        "sqlalchemy.url"
    ] = tenant_database_url

    connectable = (
        async_engine_from_config(
            configuration,
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )
    )

    try:
        async with (
            connectable.connect()
            as connection
        ):
            await connection.run_sync(
                do_run_migrations
            )

    finally:
        await connectable.dispose()


# =========================================================
# ONLINE ENTRYPOINT
# =========================================================


def run_migrations_online() -> None:
    """
    Execute tenant migrations against the selected tenant DB.
    """

    asyncio.run(
        run_async_migrations()
    )


# =========================================================
# ENTRYPOINT
# =========================================================


if context.is_offline_mode():
    run_migrations_offline()

else:
    run_migrations_online()