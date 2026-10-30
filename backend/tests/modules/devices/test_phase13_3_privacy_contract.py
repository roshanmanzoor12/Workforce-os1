from __future__ import annotations

from typing import Any

from tests.modules.devices.phase13_3_agent_signal_contract import (
    EXPECTED_AGENT_SIGNAL_ENDPOINTS,
    FORBIDDEN_ACTIVITY_FIELDS,
    FORBIDDEN_APPLICATION_FIELDS,
)
from tests.modules.devices.phase13_3_openapi_helpers import (
    openapi_schema,
    operation,
)


# =========================================================
# FORBIDDEN FIELDS
# =========================================================


FORBIDDEN_FIELDS = (
    FORBIDDEN_ACTIVITY_FIELDS
    | FORBIDDEN_APPLICATION_FIELDS
)


# =========================================================
# OPENAPI REF HELPERS
# =========================================================


def _resolve_ref(
    root_schema: dict[str, Any],
    ref: str,
) -> Any:
    """
    Resolve one local OpenAPI JSON reference.

    Only local '#/...' references are accepted because the application
    OpenAPI document is self-contained.
    """

    if not ref.startswith(
        "#/"
    ):
        raise AssertionError(
            f"Unsupported external OpenAPI ref: {ref}"
        )

    current: Any = (
        root_schema
    )

    for segment in (
        ref[2:].split("/")
    ):
        segment = (
            segment
            .replace(
                "~1",
                "/",
            )
            .replace(
                "~0",
                "~",
            )
        )

        if not isinstance(
            current,
            dict,
        ):
            raise AssertionError(
                f"Invalid OpenAPI ref traversal: {ref}"
            )

        if segment not in current:
            raise AssertionError(
                f"Missing OpenAPI ref target: {ref}"
            )

        current = (
            current[
                segment
            ]
        )

    return current


# =========================================================
# RECURSIVE PROPERTY EXTRACTION
# =========================================================


def _collect_schema_property_names(
    *,
    root_schema: dict[str, Any],
    value: Any,
    visited_refs: set[str] | None = None,
) -> set[str]:
    """
    Collect Pydantic/OpenAPI property names reachable from one
    operation's request/response schemas.

    This deliberately does NOT scan the complete application schema.
    Unrelated APIs may legitimately contain fields such as password.
    """

    if visited_refs is None:
        visited_refs = set()

    names: set[str] = set()

    if isinstance(
        value,
        list,
    ):
        for item in value:
            names.update(
                _collect_schema_property_names(
                    root_schema=root_schema,
                    value=item,
                    visited_refs=visited_refs,
                )
            )

        return names

    if not isinstance(
        value,
        dict,
    ):
        return names

    ref = value.get(
        "$ref"
    )

    if isinstance(
        ref,
        str,
    ):
        if ref in visited_refs:
            return names

        visited_refs.add(
            ref
        )

        resolved = _resolve_ref(
            root_schema,
            ref,
        )

        names.update(
            _collect_schema_property_names(
                root_schema=root_schema,
                value=resolved,
                visited_refs=visited_refs,
            )
        )

        return names

    properties = value.get(
        "properties"
    )

    if isinstance(
        properties,
        dict,
    ):
        for (
            property_name,
            property_schema,
        ) in properties.items():
            names.add(
                str(
                    property_name
                )
                .strip()
                .lower()
            )

            names.update(
                _collect_schema_property_names(
                    root_schema=root_schema,
                    value=property_schema,
                    visited_refs=visited_refs,
                )
            )

    for keyword in (
        "items",
        "allOf",
        "anyOf",
        "oneOf",
        "additionalProperties",
    ):
        nested = value.get(
            keyword
        )

        if nested is not None:
            names.update(
                _collect_schema_property_names(
                    root_schema=root_schema,
                    value=nested,
                    visited_refs=visited_refs,
                )
            )

    return names


# =========================================================
# OPERATION SCHEMA SURFACE
# =========================================================


def _operation_schema_surface(
    operation_item: dict[str, Any],
) -> list[Any]:
    """
    Return only schema-bearing parts of one HTTP operation.

    We intentionally exclude descriptions, examples, unrelated
    components, and the rest of the application's OpenAPI document.
    """

    surface: list[Any] = []

    request_body = (
        operation_item.get(
            "requestBody"
        )
    )

    if isinstance(
        request_body,
        dict,
    ):
        content = request_body.get(
            "content",
            {}
        )

        if isinstance(
            content,
            dict,
        ):
            for media_type in (
                content.values()
            ):
                if not isinstance(
                    media_type,
                    dict,
                ):
                    continue

                schema = media_type.get(
                    "schema"
                )

                if schema is not None:
                    surface.append(
                        schema
                    )

    responses = (
        operation_item.get(
            "responses",
            {}
        )
    )

    if isinstance(
        responses,
        dict,
    ):
        for response in (
            responses.values()
        ):
            if not isinstance(
                response,
                dict,
            ):
                continue

            content = response.get(
                "content",
                {}
            )

            if not isinstance(
                content,
                dict,
            ):
                continue

            for media_type in (
                content.values()
            ):
                if not isinstance(
                    media_type,
                    dict,
                ):
                    continue

                schema = media_type.get(
                    "schema"
                )

                if schema is not None:
                    surface.append(
                        schema
                    )

    return surface


# =========================================================
# PRIVACY CONTRACT
# =========================================================


def test_agent_signal_schemas_have_no_forbidden_capture_fields():
    root_schema = (
        openapi_schema()
    )

    failures: list[str] = []

    for (
        method,
        path,
    ) in sorted(
        EXPECTED_AGENT_SIGNAL_ENDPOINTS
    ):
        operation_item = operation(
            method=method,
            path=path,
        )

        property_names: set[
            str
        ] = set()

        for schema_surface in (
            _operation_schema_surface(
                operation_item
            )
        ):
            property_names.update(
                _collect_schema_property_names(
                    root_schema=root_schema,
                    value=schema_surface,
                )
            )

        present = sorted(
            property_names
            & FORBIDDEN_FIELDS
        )

        if present:
            failures.append(
                (
                    f"{method} {path}: "
                    + ", ".join(
                        present
                    )
                )
            )

    assert not failures, (
        "Forbidden monitoring capture fields "
        "present in agent signal contracts: "
        + "; ".join(
            failures
        )
    )