from __future__ import annotations

import asyncio
import sys
import uuid
from pathlib import Path


# =========================================================
# PROJECT IMPORT PATH
# =========================================================
#
# File:
#
#   backend/scripts/
#   phase12_1_tenant_migration_certification.py
#
# parents[1] resolves to:
#
#   backend/
#
# This allows direct execution:
#
#   python scripts/phase12_1_tenant_migration_certification.py
#
# without requiring PYTHONPATH to be set manually.
# =========================================================


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
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


from alembic import command
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    create_async_engine,
)

from app.db.tenant import (
    build_tenant_database_url,
    dispose_tenant_engine,
)
from app.db.tenant_migrations import (
    build_tenant_alembic_config,
    upgrade_tenant_database_to_head,
)
from app.db.tenant_provisioning import (
    create_postgres_admin_engine,
    create_tenant_database,
    quote_postgres_identifier,
)


# =========================================================
# REVISION CONTRACT
# =========================================================


HEAD = "m3h4i5j6k7l8"

PREVIOUS = "l2g3h4i5j6k7"


# =========================================================
# CURRENT ALEMBIC REVISION
# =========================================================


async def current_revision(
    database_name: str,
) -> str:
    engine = create_async_engine(
        build_tenant_database_url(
            database_name
        ),
        pool_pre_ping=True,
    )

    try:
        async with (
            engine.connect()
            as connection
        ):
            result = await (
                connection.execute(
                    text(
                        """
                        SELECT version_num
                        FROM alembic_version
                        """
                    )
                )
            )

            revision = (
                result.scalar_one_or_none()
            )

            if revision is None:
                raise RuntimeError(
                    "Tenant database does "
                    "not have an Alembic "
                    "revision."
                )

            return str(
                revision
            )

    finally:
        await engine.dispose()


# =========================================================
# TABLE EXISTS
# =========================================================


async def table_exists(
    database_name: str,
    table_name: str,
) -> bool:
    engine = create_async_engine(
        build_tenant_database_url(
            database_name
        ),
        pool_pre_ping=True,
    )

    try:
        async with (
            engine.connect()
            as connection
        ):
            result = await (
                connection.execute(
                    text(
                        """
                        SELECT EXISTS (
                            SELECT 1
                            FROM information_schema.tables
                            WHERE table_schema = 'public'
                              AND table_name = :table_name
                        )
                        """
                    ),
                    {
                        "table_name": (
                            table_name
                        ),
                    },
                )
            )

            return bool(
                result.scalar_one()
            )

    finally:
        await engine.dispose()


# =========================================================
# DOWNGRADE
# =========================================================


async def downgrade_to_previous(
    database_name: str,
) -> None:
    config = (
        build_tenant_alembic_config(
            database_name=database_name
        )
    )

    await asyncio.to_thread(
        command.downgrade,
        config,
        PREVIOUS,
    )

# =========================================================
# DROP DISPOSABLE DATABASE
# =========================================================


async def drop_database(
    database_name: str,
) -> None:
    # Remove any cached application engine first.
    await dispose_tenant_engine(
        database_name
    )

    engine = (
        create_postgres_admin_engine()
    )

    quoted_name = (
        quote_postgres_identifier(
            database_name
        )
    )

    try:
        async with (
            engine.connect()
            as connection
        ):
            # -------------------------------------------------
            # TERMINATE OTHER CONNECTIONS
            # -------------------------------------------------

            await connection.execute(
                text(
                    """
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = :database_name
                      AND pid <> pg_backend_pid()
                    """
                ),
                {
                    "database_name": (
                        database_name
                    ),
                },
            )

            # -------------------------------------------------
            # DROP DATABASE
            # -------------------------------------------------

            await (
                connection
                .exec_driver_sql(
                    f"DROP DATABASE "
                    f"{quoted_name}"
                )
            )

    finally:
        await engine.dispose()


# =========================================================
# CERTIFICATION
# =========================================================


async def main() -> None:
    database_name = (
        "tenant_"
        + uuid.uuid4().hex
    )

    database_created = False

    print()
    print(
        "================================================"
    )
    print(
        " WorkforceOS Phase 12.1 "
        "Tenant Migration Certification"
    )
    print(
        "================================================"
    )

    print()
    print(
        "Disposable tenant:",
        database_name,
    )

    try:
        # =================================================
        # CREATE DATABASE
        # =================================================

        print()
        print(
            "[0/6] Create disposable tenant..."
        )

        result = await (
            create_tenant_database(
                database_name
            )
        )

        database_created = True

        print(
            "PASS disposable tenant created"
        )

        print(
            "Created:",
            result.created,
        )

        print(
            "Already existed:",
            result.already_existed,
        )

        # =================================================
        # 1. UPGRADE TO HEAD
        # =================================================

        print()
        print(
            "[1/6] Upgrade tenant to head..."
        )

        await (
            upgrade_tenant_database_to_head(
                database_name
            )
        )

        revision = await (
            current_revision(
                database_name
            )
        )

        if revision != HEAD:
            raise RuntimeError(
                "Unexpected tenant revision "
                "after upgrade. "
                f"Expected={HEAD}, "
                f"Actual={revision}"
            )

        print(
            "PASS head:",
            revision,
        )

        # =================================================
        # 2. VERIFY SNAPSHOT TABLE
        # =================================================

        print()
        print(
            "[2/6] Verify publication "
            "snapshot table..."
        )

        snapshot_exists = (
            await table_exists(
                database_name,
                (
                    "schedule_"
                    "publication_days"
                ),
            )
        )

        if not snapshot_exists:
            raise RuntimeError(
                "schedule_publication_days "
                "was not created."
            )

        print(
            "PASS snapshot table exists"
        )

        # =================================================
        # 3. DOWNGRADE
        # =================================================

        print()
        print(
            "[3/6] Downgrade to "
            "previous revision..."
        )

        await downgrade_to_previous(
            database_name
        )

        revision = await (
            current_revision(
                database_name
            )
        )

        if revision != PREVIOUS:
            raise RuntimeError(
                "Unexpected tenant revision "
                "after downgrade. "
                f"Expected={PREVIOUS}, "
                f"Actual={revision}"
            )

        print(
            "PASS downgrade:",
            revision,
        )

        # =================================================
        # 4. VERIFY TABLE REMOVED
        # =================================================

        print()
        print(
            "[4/6] Verify snapshot "
            "table removed..."
        )

        snapshot_exists = (
            await table_exists(
                database_name,
                (
                    "schedule_"
                    "publication_days"
                ),
            )
        )

        if snapshot_exists:
            raise RuntimeError(
                "schedule_publication_days "
                "still exists after downgrade."
            )

        print(
            "PASS snapshot table removed"
        )

        # =================================================
        # 5. RE-UPGRADE
        # =================================================

        print()
        print(
            "[5/6] Re-upgrade tenant "
            "to head..."
        )

        await (
            upgrade_tenant_database_to_head(
                database_name
            )
        )

        revision = await (
            current_revision(
                database_name
            )
        )

        if revision != HEAD:
            raise RuntimeError(
                "Unexpected tenant revision "
                "after re-upgrade. "
                f"Expected={HEAD}, "
                f"Actual={revision}"
            )

        snapshot_exists = (
            await table_exists(
                database_name,
                (
                    "schedule_"
                    "publication_days"
                ),
            )
        )

        if not snapshot_exists:
            raise RuntimeError(
                "schedule_publication_days "
                "is missing after re-upgrade."
            )

        print(
            "PASS re-upgrade:",
            revision,
        )

        print(
            "PASS snapshot table exists "
            "after re-upgrade"
        )

        # =================================================
        # 6. FINAL CERTIFICATION
        # =================================================

        print()
        print(
            "[6/6] Certification..."
        )

        print(
            "PASS upgrade"
        )

        print(
            "PASS snapshot creation"
        )

        print(
            "PASS downgrade"
        )

        print(
            "PASS snapshot removal"
        )

        print(
            "PASS re-upgrade"
        )

    finally:
        # =================================================
        # CLEANUP
        # =================================================

        if database_created:
            print()
            print(
                "Cleaning disposable tenant..."
            )

            try:
                await drop_database(
                    database_name
                )

            except Exception as exc:
                print(
                    "WARNING disposable tenant "
                    "cleanup failed:"
                )

                print(
                    repr(
                        exc
                    )
                )

                raise

            else:
                print(
                    "PASS disposable tenant "
                    "removed"
                )

    print()
    print(
        "================================================"
    )
    print(
        " Phase 12.1 Tenant Migration "
        "Certification PASS"
    )
    print(
        "================================================"
    )


# =========================================================
# ENTRYPOINT
# =========================================================


if __name__ == "__main__":
    asyncio.run(
        main()
    )