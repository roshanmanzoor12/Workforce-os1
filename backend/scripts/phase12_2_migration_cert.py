from __future__ import annotations

import ast
import asyncio
import subprocess
import sys
from pathlib import Path
from typing import Any


# =========================================================
# PROJECT ROOT
# =========================================================

ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

root_text = str(
    ROOT
)

if root_text not in sys.path:
    sys.path.insert(
        0,
        root_text,
    )


# =========================================================
# APPLICATION IMPORTS
# =========================================================

from sqlalchemy import (
    inspect,
    text,
)

from sqlalchemy.ext.asyncio import (
    create_async_engine,
)

from app.db.tenant import (
    build_tenant_database_url,
)

from scripts.phase12_2_disposable_tenant import (
    create_disposable_database,
    drop_disposable_database,
)


# =========================================================
# PATHS / CONSTANTS
# =========================================================

ALEMBIC_INI = (
    ROOT
    / "alembic.tenant.ini"
)

VERSIONS = (
    ROOT
    / "migrations"
    / "tenant"
    / "versions"
)

HEAD_REVISION = (
    "n4i5j6k7l8m9"
)

LEAVE_TABLES = {
    "leave_types",
    "leave_policies",
    "leave_balances",
    "leave_requests",
}


# =========================================================
# MIGRATION METADATA
# =========================================================


def migration_file() -> Path:
    files = list(
        VERSIONS.glob(
            f"{HEAD_REVISION}_*.py"
        )
    )

    if len(files) != 1:
        raise RuntimeError(
            "Expected exactly one "
            "Phase 12.2 migration file; "
            f"found {len(files)}."
        )

    return files[0]


def _literal_value(
    node: ast.AST,
) -> Any:
    try:
        return ast.literal_eval(
            node
        )

    except (
        ValueError,
        TypeError,
    ) as exc:
        raise RuntimeError(
            "Migration metadata "
            "is not a literal value."
        ) from exc


def migration_assignment(
    name: str,
) -> Any:
    source = (
        migration_file()
        .read_text(
            encoding="utf-8"
        )
    )

    tree = ast.parse(
        source
    )

    for node in tree.body:

        if isinstance(
            node,
            ast.Assign,
        ):
            for target in node.targets:
                if (
                    isinstance(
                        target,
                        ast.Name,
                    )
                    and target.id
                    == name
                ):
                    return _literal_value(
                        node.value
                    )

        if isinstance(
            node,
            ast.AnnAssign,
        ):
            if (
                isinstance(
                    node.target,
                    ast.Name,
                )
                and node.target.id
                == name
            ):
                if node.value is None:
                    raise RuntimeError(
                        f"{name} has no value."
                    )

                return _literal_value(
                    node.value
                )

    raise RuntimeError(
        f"{name} was not found "
        "in Phase 12.2 migration."
    )


def get_parent_revision() -> str:
    parent = migration_assignment(
        "down_revision"
    )

    if not isinstance(
        parent,
        str,
    ):
        raise RuntimeError(
            "Phase 12.2 migration "
            "must have one string "
            "parent revision."
        )

    parent = parent.strip()

    if not parent:
        raise RuntimeError(
            "Phase 12.2 migration "
            "parent revision is empty."
        )

    if parent == HEAD_REVISION:
        raise RuntimeError(
            "Phase 12.2 migration "
            "cannot be its own parent."
        )

    return parent


def verify_revision_identity() -> None:
    revision = migration_assignment(
        "revision"
    )

    if revision != HEAD_REVISION:
        raise RuntimeError(
            "Phase 12.2 migration "
            "revision mismatch: "
            f"{revision!r}"
        )


# =========================================================
# ALEMBIC EXECUTION
# =========================================================


def run_alembic(
    database_name: str,
    *arguments: str,
) -> None:
    command = [
        sys.executable,
        "-m",
        "alembic",
        "-c",
        str(
            ALEMBIC_INI
        ),
        "-x",
        (
            "database_name="
            + database_name
        ),
        *arguments,
    ]

    print(
        "ALEMBIC:",
        " ".join(
            arguments
        ),
        flush=True,
    )

    subprocess.run(
        command,
        cwd=ROOT,
        check=True,
    )


# =========================================================
# DATABASE INSPECTION
# =========================================================


async def database_state(
    database_name: str,
) -> tuple[
    str | None,
    set[str],
]:
    url = (
        build_tenant_database_url(
            database_name
        )
    )

    engine = (
        create_async_engine(
            url,
            pool_pre_ping=True,
        )
    )

    try:
        async with engine.connect() as connection:

            def inspect_tables(
                sync_connection,
            ) -> set[str]:
                return set(
                    inspect(
                        sync_connection
                    )
                    .get_table_names()
                )

            tables = await (
                connection.run_sync(
                    inspect_tables
                )
            )

            revision: (
                str | None
            ) = None

            if (
                "alembic_version"
                in tables
            ):
                result = await (
                    connection.execute(
                        text(
                            """
                            SELECT version_num
                            FROM alembic_version
                            LIMIT 1
                            """
                        )
                    )
                )

                revision = (
                    result
                    .scalar_one_or_none()
                )

            return (
                revision,
                tables,
            )

    finally:
        await engine.dispose()


# =========================================================
# TABLE ASSERTIONS
# =========================================================


def require_leave_tables(
    tables: set[str],
) -> None:
    missing = (
        LEAVE_TABLES
        - tables
    )

    if missing:
        raise RuntimeError(
            "Missing Leave tables: "
            + ", ".join(
                sorted(
                    missing
                )
            )
        )


def require_leave_tables_absent(
    tables: set[str],
) -> None:
    remaining = (
        LEAVE_TABLES
        & tables
    )

    if remaining:
        raise RuntimeError(
            "Leave tables still exist "
            "after downgrade: "
            + ", ".join(
                sorted(
                    remaining
                )
            )
        )


# =========================================================
# CERTIFICATION
# =========================================================


async def certify() -> None:
    verify_revision_identity()

    parent = (
        get_parent_revision()
    )

    print(
        "PHASE12_2_HEAD="
        + HEAD_REVISION
    )

    print(
        "PHASE12_2_PARENT="
        + parent
    )

    database_name = (
        await
        create_disposable_database()
    )

    try:
        # ---------------------------------------------
        # FRESH DB -> HEAD
        # ---------------------------------------------

        run_alembic(
            database_name,
            "upgrade",
            "head",
        )

        (
            revision,
            tables,
        ) = await database_state(
            database_name
        )

        if (
            revision
            != HEAD_REVISION
        ):
            raise RuntimeError(
                "Unexpected revision "
                "after upgrade: "
                f"{revision!r}"
            )

        require_leave_tables(
            tables
        )

        print(
            "PASS upgrade -> "
            + HEAD_REVISION
        )

        # ---------------------------------------------
        # HEAD -> PARENT
        # ---------------------------------------------

        run_alembic(
            database_name,
            "downgrade",
            parent,
        )

        (
            revision,
            tables,
        ) = await database_state(
            database_name
        )

        if revision != parent:
            raise RuntimeError(
                "Unexpected revision "
                "after downgrade: "
                f"{revision!r}"
            )

        require_leave_tables_absent(
            tables
        )

        print(
            "PASS downgrade -> "
            + parent
        )

        # ---------------------------------------------
        # PARENT -> HEAD
        # ---------------------------------------------

        run_alembic(
            database_name,
            "upgrade",
            "head",
        )

        (
            revision,
            tables,
        ) = await database_state(
            database_name
        )

        if (
            revision
            != HEAD_REVISION
        ):
            raise RuntimeError(
                "Unexpected revision "
                "after re-upgrade: "
                f"{revision!r}"
            )

        require_leave_tables(
            tables
        )

        print(
            "PASS re-upgrade -> "
            + HEAD_REVISION
        )

        print()
        print(
            "PASS Phase 12.2 "
            "disposable tenant "
            "migration certification"
        )

    finally:
        print()
        print(
            "Cleaning disposable "
            "tenant database..."
        )

        await (
            drop_disposable_database(
                database_name
            )
        )


if __name__ == "__main__":
    asyncio.run(
        certify()
    )