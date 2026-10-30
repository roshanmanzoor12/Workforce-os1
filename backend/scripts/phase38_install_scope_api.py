from __future__ import annotations

import ast
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path


REGISTRATION_NAME = "_register_membership_scope_routes"

IMPORT_SOURCE = (
    "from app.modules.workspace_rbac.scope_registration import (\n"
    "    register_membership_scope_routes "
    "as _register_membership_scope_routes,\n"
    ")\n"
)


def is_app_router_call(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Attribute)
        and isinstance(node.value.func.value, ast.Name)
        and node.value.func.value.id == "app"
        and node.value.func.attr == "include_router"
    )


def install() -> None:
    backend_root = Path(__file__).resolve().parents[1]
    path = backend_root / "app" / "main.py"

    original_bytes = path.read_bytes()
    source = original_bytes.decode("utf-8-sig")
    tree = ast.parse(source, filename=str(path))

    existing_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == REGISTRATION_NAME
    ]

    if existing_calls:
        if len(existing_calls) != 1:
            raise SystemExit(
                "Multiple scope registrations found. "
                "No files were changed."
            )

        print("Scope API registration is already installed.")
        print("Run the F3A gate to verify application routes.")
        return

    anchors = []

    for node in tree.body:
        if not is_app_router_call(node):
            continue

        call = node.value

        if (
            call.args
            and isinstance(call.args[0], ast.Name)
            and call.args[0].id == "workspace_rbac_router"
        ):
            anchors.append(node)

    if len(anchors) != 1:
        raise SystemExit(
            "Expected one top-level workspace_rbac_router "
            "registration. No files were changed."
        )

    anchor = anchors[0]
    prefix_keywords = [
        keyword
        for keyword in anchor.value.keywords
        if keyword.arg == "prefix"
    ]

    if len(prefix_keywords) != 1:
        raise SystemExit(
            "Expected one explicit RBAC API prefix. "
            "No files were changed."
        )

    prefix_source = ast.get_source_segment(
        source,
        prefix_keywords[0].value,
    )

    if not prefix_source:
        raise SystemExit(
            "Could not read the RBAC API prefix expression. "
            "No files were changed."
        )

    # Avoid overwriting an existing binding with the installer's alias.
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id == REGISTRATION_NAME:
            raise SystemExit(
                "Scope registration alias is already used. "
                "No files were changed."
            )

        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if any(
                alias.asname == REGISTRATION_NAME
                for alias in node.names
            ):
                raise SystemExit(
                    "Scope registration import exists without its call. "
                    "No files were changed."
                )

    addition = (
        "\n\n"
        + IMPORT_SOURCE
        + "\n"
        + REGISTRATION_NAME
        + "(\n"
        + "    app,\n"
        + f"    prefix={prefix_source},\n"
        + ")\n"
    )

    lines = source.splitlines(keepends=True)
    insertion_index = anchor.end_lineno

    if not lines[insertion_index - 1].endswith(("\n", "\r")):
        lines[insertion_index - 1] += "\n"

    lines.insert(insertion_index, addition)
    updated = "".join(lines)

    compile(updated, str(path), "exec")

    timestamp = datetime.now(timezone.utc).strftime(
        "%Y%m%d_%H%M%S_%f",
    )

    backup_directory = (
        backend_root
        / "phase38_backups"
        / f"38_2f3a_{timestamp}"
    )

    backup_directory.mkdir(parents=True, exist_ok=False)
    backup = backup_directory / "main.py"
    backup.write_bytes(original_bytes)

    temporary_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix="main_phase38_",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            handle.write(updated)

        os.replace(temporary_path, path)
        temporary_path = None

    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)

    print("Updated:", path)
    print("Backup:", backup)
    print("PHASE38_SCOPE_API_REGISTRATION_SOURCE_OK")


if __name__ == "__main__":
    install()