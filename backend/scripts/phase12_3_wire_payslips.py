from __future__ import annotations

import ast
from pathlib import Path


ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)


TENANT_ENV = (
    ROOT
    / "migrations"
    / "tenant"
    / "env.py"
)


TENANT_ROUTER = (
    ROOT
    / "app"
    / "modules"
    / "tenant_api"
    / "router.py"
)


TENANT_INITIALIZATION = (
    ROOT
    / "app"
    / "db"
    / "tenant_initialization.py"
)


MODEL_IMPORT = (
    "from app.modules.payroll "
    "import payslip_models  "
    "# noqa: F401"
)


ROUTER_IMPORT = (
    "from app.modules.payroll."
    "payslip_router import "
    "router as payroll_payslip_router"
)


NEW_SCHEMA_VERSION = (
    "p6k7l8m9n0o1"
)


def read(
    path: Path,
) -> str:
    if not path.exists():
        raise RuntimeError(
            f"Missing file: {path}"
        )

    return path.read_text(
        encoding="utf-8"
    )


def write(
    path: Path,
    source: str,
) -> None:
    ast.parse(
        source
    )

    path.write_text(
        source,
        encoding="utf-8",
    )


def patch_env() -> None:
    source = read(
        TENANT_ENV
    )

    if (
        "payslip_models"
        in source
    ):
        print(
            "SKIP Payslip model metadata"
        )

        return

    marker = (
        "from app.modules.payroll "
        "import models as payroll_models"
    )

    index = source.find(
        marker
    )

    if index < 0:
        marker = (
            "# =========================================================\n"
            "# ALEMBIC CONFIG"
        )

        index = source.find(
            marker
        )

    if index < 0:
        raise RuntimeError(
            "Could not locate tenant "
            "Alembic model insertion point."
        )

    if (
        source[index:index + len(marker)]
        .startswith(
            "from app.modules.payroll"
        )
    ):
        end = source.find(
            "\n",
            index,
        )

        end = (
            end + 1
        )

        updated = (
            source[:end]
            + MODEL_IMPORT
            + "\n"
            + source[end:]
        )

    else:
        updated = (
            source[:index]
            + MODEL_IMPORT
            + "\n\n"
            + source[index:]
        )

    write(
        TENANT_ENV,
        updated,
    )

    print(
        "PATCH Payslip model metadata"
    )


def patch_router() -> None:
    source = read(
        TENANT_ROUTER
    )

    if (
        "payroll_payslip_router"
        not in source
    ):
        marker = (
            "router = APIRouter"
        )

        index = source.find(
            marker
        )

        if index < 0:
            raise RuntimeError(
                "Could not locate tenant "
                "router import point."
            )

        source = (
            source[:index]
            + ROUTER_IMPORT
            + "\n\n"
            + source[index:]
        )

    include = (
        "router.include_router(\n"
        "    payroll_payslip_router\n"
        ")"
    )

    if include not in source:
        marker = "__all__"

        index = source.find(
            marker
        )

        block = (
            "\n"
            "# =========================================================\n"
            "# PHASE 12.3 — PAYSLIPS\n"
            "# =========================================================\n"
            "\n"
            + include
            + "\n\n"
        )

        if index >= 0:
            source = (
                source[:index]
                + block
                + source[index:]
            )

        else:
            source = (
                source.rstrip()
                + "\n"
                + block
            )

    write(
        TENANT_ROUTER,
        source,
    )

    print(
        "PATCH Payslip router"
    )


def patch_schema_version() -> None:
    source = read(
        TENANT_INITIALIZATION
    )

    tree = ast.parse(
        source
    )

    node = None

    for item in tree.body:
        if isinstance(
            item,
            ast.Assign,
        ):
            if any(
                isinstance(
                    target,
                    ast.Name,
                )
                and target.id
                == (
                    "CURRENT_TENANT_"
                    "SCHEMA_VERSION"
                )
                for target
                in item.targets
            ):
                node = item
                break

        if isinstance(
            item,
            ast.AnnAssign,
        ):
            if (
                isinstance(
                    item.target,
                    ast.Name,
                )
                and item.target.id
                == (
                    "CURRENT_TENANT_"
                    "SCHEMA_VERSION"
                )
            ):
                node = item
                break

    if node is None:
        raise RuntimeError(
            "CURRENT_TENANT_SCHEMA_VERSION "
            "not found."
        )

    lines = source.splitlines()

    lines[
        node.lineno - 1:
        node.end_lineno
    ] = [
        (
            "CURRENT_TENANT_SCHEMA_VERSION "
            f'= "{NEW_SCHEMA_VERSION}"'
        )
    ]

    updated = (
        "\n".join(
            lines
        )
        + "\n"
    )

    write(
        TENANT_INITIALIZATION,
        updated,
    )

    print(
        "PATCH tenant schema version"
    )


def main() -> None:
    patch_env()

    patch_router()

    patch_schema_version()

    print()
    print(
        "PASS Phase 12.3 Payslip wiring"
    )


if __name__ == "__main__":
    main()