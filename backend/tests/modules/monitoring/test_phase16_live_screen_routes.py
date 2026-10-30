from __future__ import annotations

from app.main import app

from tests.modules.monitoring.phase16_live_screen_contract import (
    LIVE_SCREEN_ENDPOINTS,
)


HTTP_METHODS = {
    "get",
    "post",
    "put",
    "patch",
    "delete",
}


def test_live_screen_routes_exist():
    schema = app.openapi()

    paths = schema[
        "paths"
    ]

    missing: list[str] = []

    for (
        method,
        path,
    ) in sorted(
        LIVE_SCREEN_ENDPOINTS
    ):
        item = paths.get(
            path
        )

        if not isinstance(
            item,
            dict,
        ):
            missing.append(
                f"{method} {path}"
            )

            continue

        if (
            method.lower()
            not in item
        ):
            missing.append(
                f"{method} {path}"
            )

    assert not missing, (
        "Missing Live Screen routes: "
        + "; ".join(
            missing
        )
    )


def test_live_screen_mutation_methods_are_post():
    schema = app.openapi()

    paths = schema[
        "paths"
    ]

    lifecycle_suffixes = (
        "/live-sessions",
        "/decision",
        "/activate",
        "/end",
    )

    failures: list[str] = []

    for path, item in (
        paths.items()
    ):
        if (
            "/live-monitoring/live-sessions"
            not in path
        ):
            continue

        if not any(
            path.endswith(
                suffix
            )
            for suffix
            in lifecycle_suffixes
        ):
            continue

        methods = {
            method.lower()
            for method
            in item.keys()
            if method.lower()
            in HTTP_METHODS
        }

        if path.endswith(
            "/{session_id}"
        ):
            continue

        if methods != {
            "post"
        }:
            failures.append(
                (
                    f"{path}: "
                    f"{sorted(methods)}"
                )
            )

    assert not failures, (
        "Invalid Live Screen mutation "
        "methods: "
        + "; ".join(
            failures
        )
    )