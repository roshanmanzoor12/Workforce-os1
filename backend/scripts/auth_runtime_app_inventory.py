from __future__ import annotations

import importlib
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.routing import APIRoute


BACKEND_ROOT = Path(
    r"C:\workforce-os\backend"
)

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(BACKEND_ROOT),
    )


CANDIDATE_MODULES = (
    "main",
    "app.main",
)

AUTH_TOKENS = (
    "auth",
    "login",
    "logout",
    "register",
    "signup",
    "verify",
    "verification",
    "otp",
    "forgot",
    "reset",
    "password",
    "google",
    "github",
    "oauth",
    "refresh",
    "token",
)


def load_candidate(
    module_name: str,
) -> FastAPI | None:
    try:
        module = importlib.import_module(
            module_name
        )
    except Exception as exc:
        print(
            f"IMPORT FAIL {module_name}: "
            f"{type(exc).__name__}: {exc}"
        )

        return None

    app = getattr(
        module,
        "app",
        None,
    )

    if not isinstance(
        app,
        FastAPI,
    ):
        print(
            f"NO FASTAPI APP {module_name}"
        )

        return None

    return app


def get_api_routes(
    app: FastAPI,
) -> list[APIRoute]:
    return [
        route
        for route in app.routes
        if isinstance(
            route,
            APIRoute,
        )
    ]


def is_auth_route(
    route: APIRoute,
) -> bool:
    path = route.path.lower()

    name = (
        route.name
        or ""
    ).lower()

    tags = " ".join(
        str(tag).lower()
        for tag in (
            route.tags
            or []
        )
    )

    searchable = (
        f"{path} "
        f"{name} "
        f"{tags}"
    )

    return any(
        token in searchable
        for token in AUTH_TOKENS
    )


def print_route(
    route: APIRoute,
) -> None:
    methods = ",".join(
        sorted(
            route.methods
            or []
        )
    )

    tags = ",".join(
        str(tag)
        for tag in (
            route.tags
            or []
        )
    )

    print(
        f"{methods:14} "
        f"{route.path:65} "
        f"name={route.name!r} "
        f"tags={tags!r}"
    )


def print_flow_coverage(
    routes: list[APIRoute],
) -> None:
    paths = [
        route.path.lower()
        for route in routes
    ]

    checks = {
        "login": (
            "login",
        ),
        "register/signup": (
            "register",
            "signup",
        ),
        "email verification": (
            "verify",
            "verification",
            "otp",
        ),
        "forgot password": (
            "forgot",
        ),
        "reset password": (
            "reset",
        ),
        "refresh token": (
            "refresh",
        ),
        "google oauth": (
            "google",
        ),
    }

    for label, tokens in checks.items():
        found = any(
            token in path
            for path in paths
            for token in tokens
        )

        status = (
            "PASS"
            if found
            else "MISSING"
        )

        print(
            f"{status:8} {label}"
        )


def find_router_files() -> list[Path]:
    app_root = (
        BACKEND_ROOT
        / "app"
    )

    matches: list[Path] = []

    for path in app_root.rglob(
        "*.py"
    ):
        try:
            text = path.read_text(
                encoding="utf-8"
            )
        except UnicodeDecodeError:
            text = path.read_text(
                encoding="utf-8-sig"
            )

        if (
            "APIRouter(" in text
            or "@router." in text
            or "include_router(" in text
        ):
            matches.append(
                path
            )

    return sorted(
        matches
    )


def inspect_router_file(
    path: Path,
) -> None:
    text = path.read_text(
        encoding="utf-8-sig"
    )

    interesting_tokens = (
        "APIRouter(",
        "prefix=",
        "@router.",
        "include_router(",
        "google",
        "forgot",
        "reset",
        "verify",
        "register",
        "signup",
        "login",
        "refresh",
    )

    lines: list[
        tuple[int, str]
    ] = []

    for line_number, raw_line in enumerate(
        text.splitlines(),
        start=1,
    ):
        line = raw_line.strip()

        if any(
            token.lower()
            in line.lower()
            for token
            in interesting_tokens
        ):
            lines.append(
                (
                    line_number,
                    line,
                )
            )

    if not lines:
        return

    print()
    print(
        "FILE:",
        path.relative_to(
            BACKEND_ROOT
        ),
    )

    for line_number, line in lines:
        print(
            f"  {line_number:4}: {line}"
        )


def main() -> None:
    print()
    print(
        "============================================================"
    )
    print(
        " WorkforceOS Runtime FastAPI App Inventory"
    )
    print(
        "============================================================"
    )
    print()

    winner_name: str | None = None
    winner_routes: list[APIRoute] = []

    for module_name in CANDIDATE_MODULES:
        print(
            f"[APP] {module_name}"
        )

        app = load_candidate(
            module_name
        )

        if app is None:
            print()
            continue

        routes = get_api_routes(
            app
        )

        print(
            f"FastAPI routes: {len(routes)}"
        )

        for route in sorted(
            routes,
            key=lambda item: item.path,
        ):
            print_route(
                route
            )

        print()

        if len(routes) > len(
            winner_routes
        ):
            winner_name = module_name
            winner_routes = routes

    print(
        "============================================================"
    )
    print(
        " MOST LIKELY RUNTIME APP"
    )
    print(
        "============================================================"
    )
    print()

    if winner_name is None:
        print(
            "FAIL no FastAPI application candidate found."
        )
    else:
        print(
            f"Selected module: {winner_name}"
        )

        print(
            f"Route count: {len(winner_routes)}"
        )

        print()

        auth_routes = [
            route
            for route in winner_routes
            if is_auth_route(
                route
            )
        ]

        print(
            "AUTH ROUTES"
        )
        print()

        if not auth_routes:
            print(
                "FAIL no auth routes registered "
                "on selected runtime app."
            )
        else:
            for route in sorted(
                auth_routes,
                key=lambda item: item.path,
            ):
                print_route(
                    route
                )

        print()
        print(
            "FLOW COVERAGE"
        )
        print()

        print_flow_coverage(
            auth_routes
        )

    print()
    print(
        "============================================================"
    )
    print(
        " ROUTER SOURCE INVENTORY"
    )
    print(
        "============================================================"
    )

    router_files = find_router_files()

    if not router_files:
        print()
        print(
            "FAIL no APIRouter source files found."
        )
    else:
        for path in router_files:
            inspect_router_file(
                path
            )

    print()
    print(
        "============================================================"
    )
    print(
        " INVENTORY COMPLETE"
    )
    print(
        "============================================================"
    )
    print()


if __name__ == "__main__":
    main()