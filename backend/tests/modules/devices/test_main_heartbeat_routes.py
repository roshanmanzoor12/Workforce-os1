from __future__ import annotations

from app.main import app


def test_main_application_exposes_heartbeat_route() -> None:
    schema = app.openapi()

    paths = schema["paths"]

    path = (
        "/api/v1/device-agent/heartbeat"
    )

    assert path in paths

    assert (
        "post"
        in paths[path]
    )


def test_main_application_exposes_presence_route() -> None:
    schema = app.openapi()

    paths = schema["paths"]

    path = (
        "/api/v1/device-agent/presence"
    )

    assert path in paths

    assert (
        "get"
        in paths[path]
    )


def test_main_heartbeat_operation_contract() -> None:
    schema = app.openapi()

    operation = schema[
        "paths"
    ][
        "/api/v1/device-agent/heartbeat"
    ][
        "post"
    ]

    assert (
        operation["summary"]
        == "Send authenticated device heartbeat"
    )

    assert (
        operation["operationId"]
        .startswith(
            "device_heartbeat"
        )
    )


def test_main_presence_operation_contract() -> None:
    schema = app.openapi()

    operation = schema[
        "paths"
    ][
        "/api/v1/device-agent/presence"
    ][
        "get"
    ]

    assert (
        operation["summary"]
        == "Get authenticated device presence"
    )

    assert (
        operation["operationId"]
        .startswith(
            "get_device_presence"
        )
    )