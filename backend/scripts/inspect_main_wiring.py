from __future__ import annotations

import ast
import inspect
import sys
from pathlib import Path


BACKEND_ROOT = Path(
    r"C:\workforce-os\backend"
)

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(BACKEND_ROOT),
    )


import app.main as main_module


MAIN_FILE = Path(
    inspect.getsourcefile(
        main_module
    )
    or BACKEND_ROOT / "app" / "main.py"
)


def print_section(
    title: str,
) -> None:
    print()
    print(
        "=" * 72
    )
    print(
        f" {title}"
    )
    print(
        "=" * 72
    )
    print()


def print_source() -> str:
    source = MAIN_FILE.read_text(
        encoding="utf-8-sig",
    )

    print_section(
        "app/main.py COMPLETE SOURCE WITH LINE NUMBERS"
    )

    for line_number, line in enumerate(
        source.splitlines(),
        start=1,
    ):
        print(
            f"{line_number:4}: {line}"
        )

    return source


def inspect_ast(
    source: str,
) -> None:
    print_section(
        "AST STRUCTURE"
    )

    tree = ast.parse(
        source,
        filename=str(
            MAIN_FILE
        ),
    )

    for node in tree.body:
        if isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        ):
            print(
                f"FUNCTION "
                f"{node.name} "
                f"lines {node.lineno}-{node.end_lineno}"
            )

            for child in ast.walk(
                node
            ):
                if not isinstance(
                    child,
                    ast.Call,
                ):
                    continue

                function = child.func

                if (
                    isinstance(
                        function,
                        ast.Attribute,
                    )
                    and function.attr == "include_router"
                ):
                    print(
                        "  include_router "
                        f"inside {node.name} "
                        f"at line {child.lineno}"
                    )

        elif isinstance(
            node,
            ast.Assign,
        ):
            for target in node.targets:
                if (
                    isinstance(
                        target,
                        ast.Name,
                    )
                    and target.id == "app"
                ):
                    print(
                        f"TOP-LEVEL app assignment "
                        f"at line {node.lineno}"
                    )

        elif isinstance(
            node,
            ast.AnnAssign,
        ):
            if (
                isinstance(
                    node.target,
                    ast.Name,
                )
                and node.target.id == "app"
            ):
                print(
                    f"TOP-LEVEL annotated app assignment "
                    f"at line {node.lineno}"
                )

        elif isinstance(
            node,
            ast.Expr,
        ):
            expression = node.value

            if not isinstance(
                expression,
                ast.Call,
            ):
                continue

            function = expression.func

            if (
                isinstance(
                    function,
                    ast.Attribute,
                )
                and function.attr == "include_router"
            ):
                print(
                    "TOP-LEVEL include_router "
                    f"at line {expression.lineno}"
                )


def inspect_globals() -> None:
    print_section(
        "MODULE GLOBALS"
    )

    interesting_names = (
        "app",
        "create_app",
        "create_application",
        "build_app",
        "configure_app",
        "register_routes",
        "register_routers",
        "setup_routes",
        "api_router",
        "auth_router",
    )

    for name in interesting_names:
        if not hasattr(
            main_module,
            name,
        ):
            continue

        value = getattr(
            main_module,
            name,
        )

        print(
            f"{name}: "
            f"{type(value).__module__}."
            f"{type(value).__name__}"
        )

        if callable(
            value
        ):
            try:
                signature = inspect.signature(
                    value
                )

                print(
                    f"  signature: {signature}"
                )
            except Exception:
                pass


def inspect_runtime_app() -> None:
    print_section(
        "RUNTIME FASTAPI APP"
    )

    app = getattr(
        main_module,
        "app",
        None,
    )

    if app is None:
        print(
            "FAIL app.main has no global app object."
        )

        return

    print(
        "App object ID:",
        id(
            app
        ),
    )

    print(
        "App title:",
        getattr(
            app,
            "title",
            None,
        ),
    )

    print(
        "Total routes:",
        len(
            app.routes
        ),
    )

    for route in app.routes:
        path = getattr(
            route,
            "path",
            None,
        )

        methods = getattr(
            route,
            "methods",
            None,
        )

        route_name = getattr(
            route,
            "name",
            None,
        )

        print(
            f"  path={path!r} "
            f"methods={methods!r} "
            f"name={route_name!r}"
        )


def inspect_router_modules() -> None:
    print_section(
        "KNOWN ROUTER MODULES"
    )

    candidates = (
        (
            "auth",
            "app.modules.auth.router",
        ),
        (
            "health",
            "app.modules.health.router",
        ),
        (
            "workspaces",
            "app.modules.workspaces.router",
        ),
        (
            "employees",
            "app.modules.employees.router",
        ),
        (
            "devices",
            "app.modules.devices.router",
        ),
        (
            "activity",
            "app.modules.activity.activity_api_router",
        ),
    )

    import importlib

    for label, module_name in candidates:
        try:
            module = importlib.import_module(
                module_name
            )
        except Exception as exc:
            print(
                f"{label}: IMPORT FAIL "
                f"{type(exc).__name__}: {exc}"
            )

            continue

        router = getattr(
            module,
            "router",
            None,
        )

        if router is None:
            print(
                f"{label}: NO router OBJECT"
            )

            continue

        print(
            f"{label}: "
            f"{len(router.routes)} router route(s)"
        )

        for route in router.routes:
            print(
                "  "
                f"{getattr(route, 'path', None)} "
                f"{getattr(route, 'methods', None)}"
            )


def main() -> None:
    print()
    print(
        "============================================================"
    )
    print(
        " WorkforceOS FastAPI Main Wiring Diagnostic"
    )
    print(
        "============================================================"
    )

    print()
    print(
        "Main file:",
        MAIN_FILE,
    )

    source = print_source()

    inspect_ast(
        source
    )

    inspect_globals()

    inspect_runtime_app()

    inspect_router_modules()

    print_section(
        "DIAGNOSTIC COMPLETE"
    )

    print(
        "This diagnostic does not modify WorkforceOS."
    )

    print(
        "Use its output to repair app assembly without "
        "rewriting working router modules."
    )

    print()


if __name__ == "__main__":
    main()