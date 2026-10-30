from __future__ import annotations

from typing import Any

from fastapi import FastAPI


def load_app() -> FastAPI:
    from app.main import app

    if not isinstance(
        app,
        FastAPI,
    ):
        raise AssertionError(
            "app.main.app is not FastAPI."
        )

    return app


def schema() -> dict[str, Any]:
    result = load_app().openapi()

    if not isinstance(
        result,
        dict,
    ):
        raise AssertionError(
            "OpenAPI schema unavailable."
        )

    return result


def paths() -> dict[str, Any]:
    result = schema().get(
        "paths"
    )

    if not isinstance(
        result,
        dict,
    ):
        raise AssertionError(
            "OpenAPI paths unavailable."
        )

    return result


def operation(
    *,
    method: str,
    path: str,
) -> dict[str, Any]:
    path_item = paths().get(
        path
    )

    if not isinstance(
        path_item,
        dict,
    ):
        raise AssertionError(
            f"Missing path: {path}"
        )

    result = path_item.get(
        method.lower()
    )

    if not isinstance(
        result,
        dict,
    ):
        raise AssertionError(
            f"Missing {method.upper()} {path}"
        )

    return result


__all__ = [
    "load_app",
    "schema",
    "paths",
    "operation",
]