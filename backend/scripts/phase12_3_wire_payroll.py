from __future__ import annotations

import ast
import re
from pathlib import Path


# =========================================================
# PROJECT ROOT
# =========================================================


ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)


# =========================================================
# TARGET FILES
# =========================================================


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


# =========================================================
# PAYROLL WIRING CONSTANTS
# =========================================================


PAYROLL_MODEL_IMPORT = (
    "from app.modules.payroll "
    "import models as payroll_models  "
    "# noqa: F401"
)


PAYROLL_ROUTER_IMPORT = (
    "from app.modules.payroll.router "
    "import router as payroll_router"
)


PAYROLL_ROUTER_INCLUDE = (
    "router.include_router(\n"
    "    payroll_router\n"
    ")"
)


NEW_SCHEMA_VERSION = (
    "o5j6k7l8m9n0"
)


# =========================================================
# FILE HELPERS
# =========================================================


def read(
    path: Path,
) -> str:
    if not path.exists():
        raise RuntimeError(
            f"Required file missing: {path}"
        )

    return path.read_text(
        encoding="utf-8"
    )


def write(
    path: Path,
    source: str,
) -> None:
    path.write_text(
        source,
        encoding="utf-8",
    )


# =========================================================
# AST HELPERS
# =========================================================


def parse_source(
    source: str,
    *,
    label: str,
) -> ast.Module:
    try:
        return ast.parse(
            source
        )

    except SyntaxError as exc:
        raise RuntimeError(
            f"{label} contains invalid "
            "Python syntax."
        ) from exc


def assignment_value(
    source: str,
    name: str,
):
    """
    Read either:

        NAME = value

    or:

        NAME: str = value

    Supports multiline / parenthesized assignments.
    """

    tree = parse_source(
        source,
        label=name,
    )

    for node in tree.body:

        # -------------------------------------------------
        # NAME = value
        # -------------------------------------------------

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
                    try:
                        return (
                            ast.literal_eval(
                                node.value
                            )
                        )

                    except (
                        ValueError,
                        TypeError,
                    ):
                        return None

        # -------------------------------------------------
        # NAME: type = value
        # -------------------------------------------------

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
                    return None

                try:
                    return (
                        ast.literal_eval(
                            node.value
                        )
                    )

                except (
                    ValueError,
                    TypeError,
                ):
                    return None

    return None


def find_assignment_node(
    source: str,
    name: str,
) -> (
    ast.Assign
    | ast.AnnAssign
    | None
):
    tree = parse_source(
        source,
        label=name,
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
                    return node

        elif isinstance(
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
                return node

    return None


# =========================================================
# TENANT ALEMBIC METADATA PATCH
# =========================================================


def patch_tenant_env() -> None:
    source = read(
        TENANT_ENV
    )

    # -----------------------------------------------------
    # Already wired
    # -----------------------------------------------------

    if (
        "app.modules.payroll"
        in source
        and "payroll_models"
        in source
    ):
        print(
            "SKIP Payroll Alembic metadata"
        )

        return

    # -----------------------------------------------------
    # Preferred insertion:
    # before ALEMBIC CONFIG section.
    # -----------------------------------------------------

    markers = [
        (
            "# =========================================================\n"
            "# ALEMBIC CONFIG\n"
            "# ========================================================="
        ),
        "config = context.config",
        "target_metadata",
    ]

    for marker in markers:
        index = source.find(
            marker
        )

        if index < 0:
            continue

        addition = (
            PAYROLL_MODEL_IMPORT
            + "\n\n\n"
        )

        updated = (
            source[:index]
            + addition
            + source[index:]
        )

        # Verify resulting Python before write.
        parse_source(
            updated,
            label=(
                "migrations/tenant/env.py"
            ),
        )

        write(
            TENANT_ENV,
            updated,
        )

        print(
            "PATCH Payroll Alembic metadata"
        )

        return

    raise RuntimeError(
        "Unable to locate safe insertion "
        "point in migrations/tenant/env.py."
    )


# =========================================================
# TENANT ROUTER IMPORT PATCH
# =========================================================


def patch_router_import() -> None:
    source = read(
        TENANT_ROUTER
    )

    # -----------------------------------------------------
    # Already imported
    # -----------------------------------------------------

    tree = parse_source(
        source,
        label=(
            "tenant_api/router.py"
        ),
    )

    for node in ast.walk(
        tree
    ):
        if not isinstance(
            node,
            ast.ImportFrom,
        ):
            continue

        if (
            node.module
            != "app.modules.payroll.router"
        ):
            continue

        for alias in node.names:
            if (
                alias.name == "router"
                and alias.asname
                == "payroll_router"
            ):
                print(
                    "SKIP Payroll router import"
                )

                return

    # -----------------------------------------------------
    # Preferred insertion:
    # before router = APIRouter(...)
    # -----------------------------------------------------

    match = re.search(
        r"^router\s*=\s*APIRouter",
        source,
        flags=re.MULTILINE,
    )

    if match is not None:
        index = match.start()

        updated = (
            source[:index]
            + PAYROLL_ROUTER_IMPORT
            + "\n\n"
            + source[index:]
        )

        parse_source(
            updated,
            label=(
                "tenant_api/router.py"
            ),
        )

        write(
            TENANT_ROUTER,
            updated,
        )

        print(
            "PATCH Payroll router import"
        )

        return

    # -----------------------------------------------------
    # Fallback:
    # before first router.include_router(...)
    # -----------------------------------------------------

    match = re.search(
        r"^router\.include_router\s*\(",
        source,
        flags=re.MULTILINE,
    )

    if match is not None:
        index = match.start()

        updated = (
            source[:index]
            + PAYROLL_ROUTER_IMPORT
            + "\n\n"
            + source[index:]
        )

        parse_source(
            updated,
            label=(
                "tenant_api/router.py"
            ),
        )

        write(
            TENANT_ROUTER,
            updated,
        )

        print(
            "PATCH Payroll router import"
        )

        return

    raise RuntimeError(
        "Unable to locate tenant router "
        "import insertion point."
    )


# =========================================================
# TENANT ROUTER REGISTRATION PATCH
# =========================================================


def payroll_router_registered(
    source: str,
) -> bool:
    tree = parse_source(
        source,
        label=(
            "tenant_api/router.py"
        ),
    )

    for node in ast.walk(
        tree
    ):
        if not isinstance(
            node,
            ast.Call,
        ):
            continue

        function = node.func

        if not isinstance(
            function,
            ast.Attribute,
        ):
            continue

        if (
            function.attr
            != "include_router"
        ):
            continue

        owner = function.value

        if not (
            isinstance(
                owner,
                ast.Name,
            )
            and owner.id == "router"
        ):
            continue

        if not node.args:
            continue

        first = node.args[0]

        if (
            isinstance(
                first,
                ast.Name,
            )
            and first.id
            == "payroll_router"
        ):
            return True

    return False


def patch_router_registration() -> None:
    source = read(
        TENANT_ROUTER
    )

    if payroll_router_registered(
        source
    ):
        print(
            "SKIP Payroll router registration"
        )

        return

    block = (
        "\n"
        "# =========================================================\n"
        "# PHASE 12.3 — PAYROLL\n"
        "# =========================================================\n"
        "\n"
        + PAYROLL_ROUTER_INCLUDE
        + "\n"
    )

    # -----------------------------------------------------
    # Preferred insertion before __all__
    # -----------------------------------------------------

    match = re.search(
        r"^__all__\s*=",
        source,
        flags=re.MULTILINE,
    )

    if match is not None:
        index = match.start()

        updated = (
            source[:index]
            + block
            + "\n"
            + source[index:]
        )

        parse_source(
            updated,
            label=(
                "tenant_api/router.py"
            ),
        )

        write(
            TENANT_ROUTER,
            updated,
        )

        print(
            "PATCH Payroll router registration"
        )

        return

    # -----------------------------------------------------
    # Final fallback:
    # append at EOF.
    # -----------------------------------------------------

    updated = (
        source.rstrip()
        + "\n"
        + block
        + "\n"
    )

    parse_source(
        updated,
        label=(
            "tenant_api/router.py"
        ),
    )

    write(
        TENANT_ROUTER,
        updated,
    )

    print(
        "PATCH Payroll router registration"
    )


# =========================================================
# TENANT SCHEMA VERSION PATCH
# =========================================================


def patch_schema_version() -> None:
    source = read(
        TENANT_INITIALIZATION
    )

    assignment_node = (
        find_assignment_node(
            source,
            (
                "CURRENT_TENANT_"
                "SCHEMA_VERSION"
            ),
        )
    )

    if assignment_node is None:
        raise RuntimeError(
            "Unable to locate "
            "CURRENT_TENANT_SCHEMA_VERSION "
            "assignment."
        )

    current_value = (
        assignment_value(
            source,
            (
                "CURRENT_TENANT_"
                "SCHEMA_VERSION"
            ),
        )
    )

    if current_value == (
        NEW_SCHEMA_VERSION
    ):
        print(
            "SKIP tenant schema version"
        )

        return

    start_line = (
        assignment_node.lineno
        - 1
    )

    end_line = (
        assignment_node.end_lineno
        or assignment_node.lineno
    )

    lines = source.splitlines()

    lines[
        start_line:end_line
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

    parse_source(
        updated,
        label=(
            "tenant_initialization.py"
        ),
    )

    write(
        TENANT_INITIALIZATION,
        updated,
    )

    print(
        "PATCH tenant schema version"
    )


# =========================================================
# VALIDATION — ALEMBIC MODEL IMPORT
# =========================================================


def validate_payroll_model_import(
    source: str,
) -> None:
    tree = parse_source(
        source,
        label=(
            "migrations/tenant/env.py"
        ),
    )

    found = False

    for node in ast.walk(
        tree
    ):
        if not isinstance(
            node,
            ast.ImportFrom,
        ):
            continue

        if (
            node.module
            != "app.modules.payroll"
        ):
            continue

        for alias in node.names:
            if (
                alias.name == "models"
                and alias.asname
                == "payroll_models"
            ):
                found = True
                break

        if found:
            break

    if not found:
        raise RuntimeError(
            "Payroll model registration "
            "validation failed."
        )


# =========================================================
# VALIDATION — TARGET METADATA
# =========================================================


def validate_target_metadata(
    source: str,
) -> None:
    """
    Accept structurally equivalent formatting such as:

        target_metadata = TenantBase.metadata

    or:

        target_metadata = (
            TenantBase.metadata
        )
    """

    tree = parse_source(
        source,
        label=(
            "migrations/tenant/env.py"
        ),
    )

    assignment_found = False
    target_valid = False

    for node in tree.body:
        targets: list[
            ast.expr
        ] = []

        value: (
            ast.expr | None
        ) = None

        if isinstance(
            node,
            ast.Assign,
        ):
            targets = list(
                node.targets
            )

            value = node.value

        elif isinstance(
            node,
            ast.AnnAssign,
        ):
            targets = [
                node.target
            ]

            value = node.value

        else:
            continue

        is_target_metadata = any(
            (
                isinstance(
                    target,
                    ast.Name,
                )
                and target.id
                == "target_metadata"
            )
            for target in targets
        )

        if not is_target_metadata:
            continue

        assignment_found = True

        if value is None:
            break

        # ---------------------------------------------
        # TenantBase.metadata
        # ---------------------------------------------

        if (
            isinstance(
                value,
                ast.Attribute,
            )
            and value.attr
            == "metadata"
            and isinstance(
                value.value,
                ast.Name,
            )
            and value.value.id
            == "TenantBase"
        ):
            target_valid = True

        break

    if not assignment_found:
        raise RuntimeError(
            "Tenant Alembic target_metadata "
            "assignment was not found."
        )

    if not target_valid:
        raise RuntimeError(
            "Tenant Alembic target_metadata "
            "is not TenantBase.metadata."
        )


# =========================================================
# VALIDATION — ROUTER IMPORT
# =========================================================


def validate_router_import(
    source: str,
) -> None:
    tree = parse_source(
        source,
        label=(
            "tenant_api/router.py"
        ),
    )

    found = False

    for node in ast.walk(
        tree
    ):
        if not isinstance(
            node,
            ast.ImportFrom,
        ):
            continue

        if (
            node.module
            != "app.modules.payroll.router"
        ):
            continue

        for alias in node.names:
            if (
                alias.name == "router"
                and alias.asname
                == "payroll_router"
            ):
                found = True
                break

        if found:
            break

    if not found:
        raise RuntimeError(
            "Payroll router import "
            "validation failed."
        )


# =========================================================
# VALIDATION — SCHEMA VERSION
# =========================================================


def validate_schema_version(
    source: str,
) -> None:
    value = assignment_value(
        source,
        (
            "CURRENT_TENANT_"
            "SCHEMA_VERSION"
        ),
    )

    if value != NEW_SCHEMA_VERSION:
        raise RuntimeError(
            "Tenant schema version "
            "validation failed. "
            f"Expected "
            f"{NEW_SCHEMA_VERSION!r}; "
            f"found {value!r}."
        )


# =========================================================
# COMPLETE WIRING VALIDATION
# =========================================================


def validate_wiring() -> None:
    # -----------------------------------------------------
    # Tenant Alembic
    # -----------------------------------------------------

    tenant_env = read(
        TENANT_ENV
    )

    validate_payroll_model_import(
        tenant_env
    )

    validate_target_metadata(
        tenant_env
    )

    # -----------------------------------------------------
    # Tenant router
    # -----------------------------------------------------

    router_source = read(
        TENANT_ROUTER
    )

    validate_router_import(
        router_source
    )

    if not payroll_router_registered(
        router_source
    ):
        raise RuntimeError(
            "Payroll router registration "
            "validation failed."
        )

    # -----------------------------------------------------
    # Runtime tenant schema
    # -----------------------------------------------------

    initialization = read(
        TENANT_INITIALIZATION
    )

    validate_schema_version(
        initialization
    )

    print(
        "PASS Payroll wiring validation"
    )


# =========================================================
# MAIN
# =========================================================


def main() -> None:
    print(
        "Phase 12.3 Payroll wiring..."
    )

    print()

    patch_tenant_env()

    patch_router_import()

    patch_router_registration()

    patch_schema_version()

    print()

    validate_wiring()

    print()

    print(
        "PASS Phase 12.3 Payroll wiring"
    )


if __name__ == "__main__":
    main()