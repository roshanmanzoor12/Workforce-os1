from __future__ import annotations

from app.main import app


HEARTBEAT_PATH = (
    "/api/v1/device-agent/heartbeat"
)

PRESENCE_PATH = (
    "/api/v1/device-agent/presence"
)


def get_schema() -> dict:
    return app.openapi()


def test_heartbeat_request_body_exists() -> None:
    schema = get_schema()

    operation = schema[
        "paths"
    ][
        HEARTBEAT_PATH
    ][
        "post"
    ]

    assert "requestBody" in operation

    content = operation[
        "requestBody"
    ][
        "content"
    ]

    assert (
        "application/json"
        in content
    )


def test_heartbeat_has_success_response() -> None:
    schema = get_schema()

    operation = schema[
        "paths"
    ][
        HEARTBEAT_PATH
    ][
        "post"
    ]

    assert (
        "200"
        in operation["responses"]
    )


def test_presence_has_success_response() -> None:
    schema = get_schema()

    operation = schema[
        "paths"
    ][
        PRESENCE_PATH
    ][
        "get"
    ]

    assert (
        "200"
        in operation["responses"]
    )


def test_heartbeat_response_schema_is_registered() -> None:
    schema = get_schema()

    schemas = schema[
        "components"
    ][
        "schemas"
    ]

    assert (
        "DeviceHeartbeatResponse"
        in schemas
    )


def test_presence_response_schema_is_registered() -> None:
    schema = get_schema()

    schemas = schema[
        "components"
    ][
        "schemas"
    ]

    assert (
        "DevicePresenceResponse"
        in schemas
    )


def test_heartbeat_request_does_not_accept_device_uuid() -> None:
    schema = get_schema()

    request_schema = schema[
        "components"
    ][
        "schemas"
    ][
        "DeviceHeartbeatRequest"
    ]

    properties = request_schema.get(
        "properties",
        {},
    )

    assert (
        "device_uuid"
        not in properties
    )

    assert (
        "workspace_id"
        not in properties
    )

    assert (
        "database_name"
        not in properties
    )