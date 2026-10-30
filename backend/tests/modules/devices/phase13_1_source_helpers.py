from __future__ import annotations

import ast
from pathlib import Path


BACKEND_ROOT = (
    Path(__file__)
    .resolve()
    .parents[3]
)


APP_ROOT = (
    BACKEND_ROOT
    / "app"
)


def app_file(
    relative_path: str,
) -> Path:
    path = (
        APP_ROOT
        / relative_path
    )

    assert path.exists(), (
        f"Required application file missing: {path}"
    )

    return path


def source_text(
    relative_path: str,
) -> str:
    return app_file(
        relative_path
    ).read_text(
        encoding="utf-8"
    )


def normalized_source(
    relative_path: str,
) -> str:
    """
    Normalize whitespace so tests do not depend on formatting.
    """

    return "".join(
        source_text(
            relative_path
        ).split()
    )


def parse_source(
    relative_path: str,
) -> ast.Module:
    return ast.parse(
        source_text(
            relative_path
        )
    )


def function_names(
    relative_path: str,
) -> set[str]:
    tree = parse_source(
        relative_path
    )

    result: set[str] = set()

    for node in ast.walk(
        tree
    ):
        if isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        ):
            result.add(
                node.name
            )

    return result


def class_names(
    relative_path: str,
) -> set[str]:
    tree = parse_source(
        relative_path
    )

    return {
        node.name
        for node
        in ast.walk(
            tree
        )
        if isinstance(
            node,
            ast.ClassDef,
        )
    }


def string_literals(
    relative_path: str,
) -> set[str]:
    tree = parse_source(
        relative_path
    )

    result: set[str] = set()

    for node in ast.walk(
        tree
    ):
        if (
            isinstance(
                node,
                ast.Constant,
            )
            and isinstance(
                node.value,
                str,
            )
        ):
            result.add(
                node.value
            )

    return result


def contains_any(
    relative_path: str,
    values: tuple[
        str,
        ...,
    ],
) -> bool:
    source = (
        normalized_source(
            relative_path
        )
        .lower()
    )

    return any(
        "".join(
            value.split()
        ).lower()
        in source
        for value in values
    )


__all__ = [
    "BACKEND_ROOT",
    "APP_ROOT",
    "app_file",
    "source_text",
    "normalized_source",
    "parse_source",
    "function_names",
    "class_names",
    "string_literals",
    "contains_any",
]