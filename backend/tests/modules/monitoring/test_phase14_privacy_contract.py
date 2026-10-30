from __future__ import annotations

from typing import Any

from tests.modules.monitoring.phase14_monitoring_overview_contract import (
    AGENT_EVIDENCE_ENDPOINTS,
    FORBIDDEN_MONITORING_FIELDS,
)
from tests.modules.monitoring.phase14_openapi_helpers import (
    operation,
    schema,
)


def _resolve_ref(
    root: dict[str, Any],
    ref: str,
) -> Any:
    assert ref.startswith(
        "#/"
    )

    current: Any = root

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

        current = current[
            segment
        ]

    return current


def _collect_properties(
    *,
    root: dict[str, Any],
    value: Any,
    visited: set[str] | None = None,
) -> set[str]:
    if visited is None:
        visited = set()

    result: set[str] = set()

    if isinstance(
        value,
        list,
    ):
        for item in value:
            result.update(
                _collect_properties(
                    root=root,
                    value=item,
                    visited=visited,
                )
            )

        return result

    if not isinstance(
        value,
        dict,
    ):
        return result

    ref = value.get(
        "$ref"
    )

    if isinstance(
        ref,
        str,
    ):
        if ref in visited:
            return result

        visited.add(
            ref
        )

        return _collect_properties(
            root=root,
            value=_resolve_ref(
                root,
                ref,
            ),
            visited=visited,
        )

    properties = value.get(
        "properties"
    )

    if isinstance(
        properties,
        dict,
    ):
        for (
            name,
            property_schema,
        ) in properties.items():
            result.add(
                str(name)
                .strip()
                .lower()
            )

            result.update(
                _collect_properties(
                    root=root,
                    value=property_schema,
                    visited=visited,
                )
            )

    for key in (
        "items",
        "allOf",
        "anyOf",
        "oneOf",
        "additionalProperties",
    ):
        if key in value:
            result.update(
                _collect_properties(
                    root=root,
                    value=value[key],
                    visited=visited,
                )
            )

    return result


def _operation_schemas(
    item: dict[str, Any],
) -> list[Any]:
    output: list[Any] = []

    request_body = item.get(
        "requestBody",
        {},
    )

    if isinstance(
        request_body,
        dict,
    ):
        for media in (
            request_body
            .get(
                "content",
                {},
            )
            .values()
        ):
            if isinstance(
                media,
                dict,
            ):
                if "schema" in media:
                    output.append(
                        media["schema"]
                    )

    responses = item.get(
        "responses",
        {},
    )

    if isinstance(
        responses,
        dict,
    ):
        for response in responses.values():
            if not isinstance(
                response,
                dict,
            ):
                continue

            content = response.get(
                "content",
                {},
            )

            if not isinstance(
                content,
                dict,
            ):
                continue

            for media in content.values():
                if (
                    isinstance(
                        media,
                        dict,
                    )
                    and "schema"
                    in media
                ):
                    output.append(
                        media["schema"]
                    )

    return output


def test_monitoring_agent_contract_has_no_forbidden_capture_fields():
    root = schema()

    failures: list[str] = []

    for (
        method,
        path,
    ) in sorted(
        AGENT_EVIDENCE_ENDPOINTS
    ):
        item = operation(
            method=method,
            path=path,
        )

        fields: set[str] = set()

        for item_schema in (
            _operation_schemas(
                item
            )
        ):
            fields.update(
                _collect_properties(
                    root=root,
                    value=item_schema,
                )
            )

        forbidden = sorted(
            fields
            & FORBIDDEN_MONITORING_FIELDS
        )

        if forbidden:
            failures.append(
                (
                    f"{method} {path}: "
                    + ", ".join(
                        forbidden
                    )
                )
            )

    assert not failures, (
        "Forbidden monitoring capture fields: "
        + "; ".join(
            failures
        )
    )