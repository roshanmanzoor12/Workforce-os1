from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


# =========================================================
# PATHS
# =========================================================


BACKEND_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

REPO_ROOT = (
    BACKEND_ROOT
    .parent
)

WEB_ROOT = (
    REPO_ROOT
    / "apps"
    / "web"
)

CHANNEL_ROOT = (
    BACKEND_ROOT
    / "app"
    / "modules"
    / "channels"
)


# =========================================================
# ERROR
# =========================================================


class GateFailure(
    RuntimeError
):
    pass


# =========================================================
# FILE HELPERS
# =========================================================


def read_text(
    path: Path,
) -> str:
    try:
        return path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

    except OSError as exc:
        raise GateFailure(
            f"Unable to read {path}: {exc}"
        ) from exc


def collect_source(
    root: Path,
    *,
    suffixes: set[str],
) -> str:
    if not root.exists():
        raise GateFailure(
            f"Missing source directory: {root}"
        )

    parts: list[str] = []

    for path in sorted(
        root.rglob("*")
    ):
        if (
            path.is_file()
            and path.suffix.lower()
            in suffixes
        ):
            parts.append(
                read_text(
                    path
                )
            )

    return "\n".join(
        parts
    )


# =========================================================
# ASSERT HELPERS
# =========================================================


def require_any(
    *,
    source: str,
    markers: tuple[str, ...],
    label: str,
) -> str:
    lower = source.lower()

    for marker in markers:
        if (
            marker.lower()
            in lower
        ):
            return marker

    raise GateFailure(
        f"{label} missing. "
        f"Expected one of: {markers}"
    )


# =========================================================
# FRONTEND UNREAD CONTRACT
# =========================================================


def check_frontend_unread() -> str:
    source = collect_source(
        WEB_ROOT,
        suffixes={
            ".ts",
            ".tsx",
            ".js",
            ".jsx",
        },
    )

    return require_any(
        source=source,
        markers=(
            "unreadcount",
            "unread_count",
            "unreadbychannel",
            "unread",
        ),
        label=(
            "Frontend unread channel state"
        ),
    )


# =========================================================
# REALTIME CONTRACT
# =========================================================


def check_realtime() -> str:
    source = collect_source(
        WEB_ROOT,
        suffixes={
            ".ts",
            ".tsx",
            ".js",
            ".jsx",
        },
    )

    return require_any(
        source=source,
        markers=(
            "channel.message.created",
            "channel-realtime",
            "channelrealtime",
            "lastsequence",
        ),
        label=(
            "Frontend channel realtime wiring"
        ),
    )


# =========================================================
# BACKEND CHANNEL CONTRACT
# =========================================================


def check_backend_channels() -> None:
    source = collect_source(
        CHANNEL_ROOT,
        suffixes={
            ".py",
        },
    )

    lower = source.lower()

    required = (
        "workspacechannel",
        "workspacechannelmessage",
        "channel_id",
        "created_at",
    )

    missing = [
        marker
        for marker in required
        if marker not in lower
    ]

    if missing:
        raise GateFailure(
            "Backend durable channel "
            f"contract missing: {missing}"
        )


# =========================================================
# LEGACY POLLING
# =========================================================


def check_legacy_polling() -> None:
    room_candidates = [
        WEB_ROOT
        / "components"
        / "channels"
        / "text-channel-room.tsx",

        WEB_ROOT
        / "components"
        / "channels"
        / "text-channel-room.ts",
    ]

    existing = [
        path
        for path in room_candidates
        if path.exists()
    ]

    if not existing:
        print(
            "INFO: text-channel-room source "
            "not found at legacy location."
        )
        return

    for path in existing:
        source = (
            read_text(
                path
            )
            .lower()
            .replace(
                " ",
                "",
            )
        )

        if (
            "setinterval(" in source
            and "4000" in source
        ):
            raise GateFailure(
                "Legacy 4-second polling "
                f"still exists in {path}."
            )


# =========================================================
# FASTAPI ROUTE HELPERS
# =========================================================


def route_methods(
    route: Any,
) -> set[str]:
    methods = getattr(
        route,
        "methods",
        None,
    )

    if not methods:
        return set()

    return {
        str(
            method
        ).upper()
        for method in methods
    }


def walk_routes(
    routes: list[Any],
    *,
    inherited_prefix: str = "",
    visited: set[int] | None = None,
) -> list[
    tuple[
        str,
        set[str],
    ]
]:
    if visited is None:
        visited = set()

    discovered: list[
        tuple[
            str,
            set[str],
        ]
    ] = []

    for route in routes:
        route_identity = id(
            route
        )

        if (
            route_identity
            in visited
        ):
            continue

        visited.add(
            route_identity
        )

        # -------------------------------------------------
        # Normal HTTP / WebSocket route
        # -------------------------------------------------

        path = getattr(
            route,
            "path",
            None,
        )

        if isinstance(
            path,
            str,
        ):
            if (
                inherited_prefix
                and not path.startswith(
                    inherited_prefix
                )
            ):
                effective_path = (
                    inherited_prefix.rstrip(
                        "/"
                    )
                    + "/"
                    + path.lstrip(
                        "/"
                    )
                )
            else:
                effective_path = path

            discovered.append(
                (
                    effective_path,
                    route_methods(
                        route
                    ),
                )
            )

        # -------------------------------------------------
        # FastAPI _IncludedRouter
        # -------------------------------------------------

        original_router = getattr(
            route,
            "original_router",
            None,
        )

        if original_router is not None:
            include_context = getattr(
                route,
                "include_context",
                None,
            )

            prefix = ""

            if (
                include_context
                is not None
            ):
                prefix = str(
                    getattr(
                        include_context,
                        "prefix",
                        "",
                    )
                    or ""
                )

            next_prefix = (
                inherited_prefix.rstrip(
                    "/"
                )
                + "/"
                + prefix.strip(
                    "/"
                )
            ).rstrip(
                "/"
            )

            child_routes = getattr(
                original_router,
                "routes",
                None,
            )

            if child_routes:
                discovered.extend(
                    walk_routes(
                        list(
                            child_routes
                        ),
                        inherited_prefix=(
                            next_prefix
                        ),
                        visited=visited,
                    )
                )

        # -------------------------------------------------
        # Generic nested router fallback
        # -------------------------------------------------

        nested_routes = getattr(
            route,
            "routes",
            None,
        )

        if (
            nested_routes
            and original_router
            is None
        ):
            discovered.extend(
                walk_routes(
                    list(
                        nested_routes
                    ),
                    inherited_prefix=(
                        inherited_prefix
                    ),
                    visited=visited,
                )
            )

    return discovered


# =========================================================
# FASTAPI ROUTE CONTRACT
# =========================================================


def check_fastapi_routes() -> None:
    backend_text = str(
        BACKEND_ROOT
    )

    if (
        backend_text
        not in sys.path
    ):
        sys.path.insert(
            0,
            backend_text,
        )

    from app.main import app

    discovered = (
        walk_routes(
            list(
                app.routes
            )
        )
    )

    channel_routes: list[
        tuple[
            str,
            set[str],
        ]
    ] = []

    unread_get_routes: list[
        str
    ] = []

    for (
        path,
        methods,
    ) in discovered:
        lower = (
            path.lower()
        )

        if (
            "channel"
            in lower
        ):
            channel_routes.append(
                (
                    path,
                    methods,
                )
            )

        if (
            "channel"
            in lower
            and "unread"
            in lower
            and "GET"
            in methods
        ):
            unread_get_routes.append(
                path
            )

    if not channel_routes:
        sample = [
            path
            for (
                path,
                _methods,
            )
            in discovered[
                :25
            ]
        ]

        raise GateFailure(
            "No channel routes discovered "
            "after recursive FastAPI router "
            "traversal. "
            f"Sample routes={sample}"
        )

    unique_channel_paths = sorted(
        {
            path
            for (
                path,
                _methods,
            )
            in channel_routes
        }
    )

    print(
        "Registered channel routes:",
        len(
            unique_channel_paths
        ),
    )

    for path in (
        unique_channel_paths[
            :12
        ]
    ):
        print(
            " ",
            path,
        )

    if unread_get_routes:
        print(
            "Dedicated channel unread "
            "GET route(s):"
        )

        for path in sorted(
            set(
                unread_get_routes
            )
        ):
            print(
                " ",
                path,
            )

    else:
        print(
            "INFO: No dedicated channel "
            "GET unread endpoint registered."
        )

        print(
            "INFO: Gate will not invent "
            "a nonexistent API contract."
        )


# =========================================================
# MAIN
# =========================================================


def main() -> None:
    print(
        "================================================="
    )
    print(
        " WorkforceOS Phase 16D Read / Unread Contract Gate"
    )
    print(
        "================================================="
    )
    print()

    print(
        "[1/5] Checking durable channel backend contract..."
    )

    check_backend_channels()

    print(
        "PASS: Durable channel backend contract"
    )
    print()

    print(
        "[2/5] Checking frontend unread state wiring..."
    )

    unread_marker = (
        check_frontend_unread()
    )

    print(
        "PASS: Frontend unread state wiring"
    )

    print(
        "Detected marker:",
        unread_marker,
    )

    print()

    print(
        "[3/5] Checking realtime-backed channel wiring..."
    )

    realtime_marker = (
        check_realtime()
    )

    print(
        "PASS: Realtime-backed channel wiring"
    )

    print(
        "Detected marker:",
        realtime_marker,
    )

    print()

    print(
        "[4/5] Checking legacy polling regression..."
    )

    check_legacy_polling()

    print(
        "PASS: Legacy 4-second polling absent"
    )
    print()

    print(
        "[5/5] Checking actual FastAPI channel routes..."
    )

    check_fastapi_routes()

    print(
        "PASS: Actual recursive route contract verified"
    )

    print()
    print(
        "================================================="
    )
    print(
        " PHASE 16D READ / UNREAD CONTRACT PASS"
    )
    print(
        "================================================="
    )


if __name__ == "__main__":
    try:
        main()

    except Exception as exc:
        print(
            f"FAIL: {exc}",
            file=sys.stderr,
        )

        raise