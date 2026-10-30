from __future__ import annotations

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


from fastapi.routing import APIRoute

from app.main import app


AUTH_TOKENS = (
    "auth",
    "login",
    "logout",
    "register",
    "signup",
    "verify",
    "verification",
    "otp",
    "password",
    "forgot",
    "reset",
    "google",
    "github",
    "oauth",
    "token",
    "refresh",
)


def route_matches_auth(
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

    haystack = (
        f"{path} "
        f"{name} "
        f"{tags}"
    )

    return any(
        token in haystack
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
        f"{route.path:60} "
        f"name={route.name!r} "
        f"tags={tags!r}"
    )


def find_source_auth_files() -> list[Path]:
    matches: list[Path] = []

    app_root = (
        BACKEND_ROOT
        / "app"
    )

    for path in app_root.rglob(
        "*.py"
    ):
        lowered = path.name.lower()

        if any(
            token in lowered
            for token in (
                "auth",
                "oauth",
                "otp",
                "password",
                "email",
            )
        ):
            matches.append(
                path
            )

    return sorted(
        matches
    )


def inspect_source_file(
    path: Path,
) -> None:
    try:
        text = path.read_text(
            encoding="utf-8"
        )
    except UnicodeDecodeError:
        text = path.read_text(
            encoding="utf-8-sig"
        )

    interesting_lines: list[
        tuple[int, str]
    ] = []

    tokens = (
        "APIRouter(",
        "include_router(",
        "@router.",
        "prefix=",
        "google",
        "forgot",
        "reset",
        "verify",
        "otp",
        "register",
        "signup",
        "login",
    )

    for line_number, raw_line in enumerate(
        text.splitlines(),
        start=1,
    ):
        line = raw_line.strip()

        if any(
            token.lower() in line.lower()
            for token in tokens
        ):
            interesting_lines.append(
                (
                    line_number,
                    line,
                )
            )

    if not interesting_lines:
        return

    relative = path.relative_to(
        BACKEND_ROOT
    )

    print()
    print(
        f"FILE: {relative}"
    )

    for line_number, line in interesting_lines:
        print(
            f"  {line_number:4}: {line}"
        )


def main() -> None:
    print()
    print(
        "============================================================"
    )
    print(
        " WorkforceOS Auth Runtime Route Inventory"
    )
    print(
        "============================================================"
    )
    print()

    api_routes = [
        route
        for route in app.routes
        if isinstance(
            route,
            APIRoute,
        )
    ]

    print(
        f"Total FastAPI APIRoutes: {len(api_routes)}"
    )
    print()

    print(
        "[1/4] ALL REGISTERED API ROUTES"
    )
    print()

    if not api_routes:
        print(
            "FAIL no APIRoutes registered."
        )
    else:
        for route in sorted(
            api_routes,
            key=lambda item: item.path,
        ):
            print_route(
                route
            )

    print()
    print(
        "[2/4] AUTH-RELATED RUNTIME ROUTES"
    )
    print()

    auth_routes = [
        route
        for route in api_routes
        if route_matches_auth(
            route
        )
    ]

    if not auth_routes:
        print(
            "FAIL no auth-related runtime routes detected."
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
        "[3/4] FLOW COVERAGE"
    )
    print()

    paths = [
        route.path.lower()
        for route in auth_routes
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

    print()
    print(
        "[4/4] AUTH-RELATED SOURCE FILES"
    )

    source_files = (
        find_source_auth_files()
    )

    if not source_files:
        print()
        print(
            "FAIL no auth-related Python files found."
        )
    else:
        for source_file in source_files:
            inspect_source_file(
                source_file
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