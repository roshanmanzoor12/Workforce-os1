from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from fastapi import FastAPI


# =========================================================
# MAIN APP
# =========================================================


def load_main_app() -> FastAPI:
    from app.main import app

    if not isinstance(
        app,
        FastAPI,
    ):
        raise AssertionError(
            "app.main.app is not a FastAPI instance."
        )

    return app


# =========================================================
# OPENAPI
# =========================================================


def openapi_schema() -> dict[str, Any]:
    app = load_main_app()

    schema = app.openapi()

    if not isinstance(
        schema,
        dict,
    ):
        raise AssertionError(
            "FastAPI OpenAPI schema is unavailable."
        )

    return schema


def openapi_paths() -> Mapping[
    str,
    Any,
]:
    paths = openapi_schema().get(
        "paths"
    )

    if not isinstance(
        paths,
        dict,
    ):
        raise AssertionError(
            "OpenAPI schema has no paths mapping."
        )

    return paths


def operation(
    *,
    method: str,
    path: str,
) -> dict[str, Any]:
    paths = openapi_paths()

    path_item = paths.get(
        path
    )

    if not isinstance(
        path_item,
        dict,
    ):
        raise AssertionError(
            f"Missing OpenAPI path: {path}"
        )

    operation_item = path_item.get(
        method.lower()
    )

    if not isinstance(
        operation_item,
        dict,
    ):
        raise AssertionError(
            f"Missing {method.upper()} "
            f"operation for {path}"
        )

    return operation_item


def schema_components() -> dict[
    str,
    Any,
]:
    schema = openapi_schema()

    components = schema.get(
        "components",
        {}
    )

    if not isinstance(
        components,
        dict,
    ):
        return {}

    schemas = components.get(
        "schemas",
        {}
    )

    if not isinstance(
        schemas,
        dict,
    ):
        return {}

    return schemas


__all__ = [
    "load_main_app",
    "openapi_schema",
    "openapi_paths",
    "operation",
    "schema_components",
]