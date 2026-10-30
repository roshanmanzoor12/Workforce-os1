from __future__ import annotations

from collections import Counter

from app.main import app


HTTP_METHODS = {
    "get",
    "post",
    "put",
    "patch",
    "delete",
    "options",
    "head",
    "trace",
}


def test_operation_ids_are_unique() -> None:
    schema = app.openapi()

    operation_ids: list[
        str
    ] = []

    for path_data in (
        schema["paths"].values()
    ):
        for (
            method,
            operation,
        ) in path_data.items():
            if (
                method.lower()
                not in HTTP_METHODS
            ):
                continue

            operation_id = (
                operation.get(
                    "operationId"
                )
            )

            if operation_id:
                operation_ids.append(
                    operation_id
                )

    counts = Counter(
        operation_ids
    )

    duplicates = {
        operation_id: count
        for (
            operation_id,
            count,
        )
        in counts.items()
        if count > 1
    }

    assert duplicates == {}


def test_ai_operation_ids_present() -> None:
    schema = app.openapi()

    paths = schema[
        "paths"
    ]

    capabilities = paths[
        (
            "/api/v1/workspaces/"
            "{workspace_id}/"
            "ai-productivity/"
            "capabilities"
        )
    ]["get"]

    run = paths[
        (
            "/api/v1/workspaces/"
            "{workspace_id}/"
            "ai-productivity/run"
        )
    ]["post"]

    assert capabilities.get(
        "operationId"
    )

    assert run.get(
        "operationId"
    )