from __future__ import annotations

from app.main import app


ACTIVITY_STATE_PATH = (
    "/api/v1/device-agent/activity-state"
)

ACTIVITY_STATUS_PATH = (
    "/api/v1/device-agent/activity-status"
)


def get_schema() -> dict:
    return app.openapi()


def test_activity_state_route_is_mounted() -> None:
    schema = get_schema()

    assert (
        ACTIVITY_STATE_PATH
        in schema["paths"]
    )

    assert (
        "post"
        in schema[
            "paths"
        ][
            ACTIVITY_STATE_PATH
        ]
    )


def test_activity_status_route_is_mounted() -> None:
    schema = get_schema()

    assert (
        ACTIVITY_STATUS_PATH
        in schema["paths"]
    )

    assert (
        "get"
        in schema[
            "paths"
        ][
            ACTIVITY_STATUS_PATH
        ]
    )


def test_activity_request_schema_is_registered() -> None:
    schema = get_schema()

    schemas = schema[
        "components"
    ][
        "schemas"
    ]

    assert (
        "ActivityStateRequest"
        in schemas
    )


def test_activity_response_schema_is_registered() -> None:
    schema = get_schema()

    schemas = schema[
        "components"
    ][
        "schemas"
    ]

    assert (
        "ActivityStateResponse"
        in schemas
    )


def test_activity_status_schema_is_registered() -> None:
    schema = get_schema()

    schemas = schema[
        "components"
    ][
        "schemas"
    ]

    assert (
        "ActivityStatusResponse"
        in schemas
    )


def test_activity_request_cannot_choose_device_identity() -> None:
    schema = get_schema()

    request_schema = schema[
        "components"
    ][
        "schemas"
    ][
        "ActivityStateRequest"
    ]

    properties = request_schema.get(
        "properties",
        {},
    )

    forbidden_fields = {
        "device_id",
        "device_uuid",
        "employee_id",
        "workspace_id",
        "database_name",
        "cluster_key",
    }

    assert forbidden_fields.isdisjoint(
        properties.keys()
    )


def test_activity_request_contains_expected_fields() -> None:
    schema = get_schema()

    properties = schema[
        "components"
    ][
        "schemas"
    ][
        "ActivityStateRequest"
    ][
        "properties"
    ]

    assert {
        "state",
        "idle_seconds",
        "last_input_at",
        "observed_at",
    } <= set(
        properties.keys()
    )