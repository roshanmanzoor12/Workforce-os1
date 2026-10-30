from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import (
    async_engine_from_config,
)
from app.modules.workspace_rbac import (
    assignment_models as workspace_role_assignment_models,
)  # noqa: F401

# =========================================================
# PROJECT IMPORT PATH
# =========================================================

# File location:
#
#     backend/migrations/control/env.py
#
# parents[2] resolves to:
#
#     backend/
#
# Alembic may execute this file outside the application's
# normal import context, so make the backend package root
# explicit.

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

from app.db.base import Base

# Import every CONTROL-PLANE ORM model module here.
#
# This is important because Alembic builds target_metadata
# from Base.metadata.
#
# Current control-plane domains:
#
#     auth / users
#     workspaces
#     workspace memberships
#     workspace invitations
#     tenant database registry
#     workspace custom roles
#     workspace custom role permissions
#     membership moderation
#     device activation codes
#     device routes

from app.modules.auth import (
    models as auth_models,
)  # noqa: F401

from app.modules.workspaces import (
    models as workspace_models,
)  # noqa: F401

from app.modules.workspace_rbac import (
    models as workspace_rbac_models,
)  # noqa: F401

from app.modules.devices import (
    activation_models
    as device_activation_models,
)  # noqa: F401

from app.modules.devices import (
    routing_models
    as device_routing_models,
)  # noqa: F401


# =========================================================
# ALEMBIC CONFIG
# =========================================================

config = context.config


# =========================================================
# CONTROL DATABASE URL
# =========================================================


def get_control_database_url() -> str:
    """
    Read the trusted control-plane PostgreSQL URL.

    Expected source:

        backend/alembic-control.ini

    This migration stream must only target workforce_control.
    """

    database_url = (
        config.get_main_option(
            "sqlalchemy.url"
        )
    )

    if not database_url:
        raise RuntimeError(
            "Control database URL is not configured. "
            "Set sqlalchemy.url in alembic-control.ini."
        )

    return database_url


CONTROL_DATABASE_URL = (
    get_control_database_url()
)


# =========================================================
# TARGET METADATA
# =========================================================

from app.modules.notes import personal_models as personal_note_models  # noqa: F401

target_metadata = Base.metadata


# =========================================================
# OFFLINE MIGRATIONS
# =========================================================


def run_migrations_offline() -> None:
    """
    Generate control-plane migration SQL without opening
    a database connection.
    """

    context.configure(
        url=CONTROL_DATABASE_URL,
        target_metadata=target_metadata,
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
# SHARED MIGRATION CONFIGURATION
# =========================================================


def do_run_migrations(
    connection: Connection,
) -> None:
    """
    Configure Alembic against workforce_control.
    """

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
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
    Apply the control-plane Alembic revision stream against
    workforce_control.
    """

    configuration = (
        config.get_section(
            config.config_ini_section,
            {},
        )
    )

    configuration[
        "sqlalchemy.url"
    ] = CONTROL_DATABASE_URL

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
    Execute control-plane migrations.
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