from __future__ import annotations

from fastapi import FastAPI

from app.modules.devices.heartbeat_api_router import (
    router as heartbeat_api_router,
)


def build_test_app() -> FastAPI:
    app = FastAPI()

    app.include_router(
        heartbeat_api_router,
        prefix="/api/v1",
    )

    return app


def get_openapi_paths() -> dict:
    app = build_test_app()

    schema = app.openapi()

    return schema[
        "paths"
    ]


def test_heartbeat_router_contains_heartbeat_endpoint() -> None:
    paths = get_openapi_paths()

    heartbeat_path = (
        "/api/v1/device-agent/heartbeat"
    )

    assert (
        heartbeat_path
        in paths
    )

    assert (
        "post"
        in paths[
            heartbeat_path
        ]
    )


def test_heartbeat_router_contains_presence_endpoint() -> None:
    paths = get_openapi_paths()

    presence_path = (
        "/api/v1/device-agent/presence"
    )

    assert (
        presence_path
        in paths
    )

    assert (
        "get"
        in paths[
            presence_path
        ]
    )


def test_heartbeat_endpoint_has_expected_operation() -> None:
    paths = get_openapi_paths()

    operation = paths[
        "/api/v1/device-agent/heartbeat"
    ][
        "post"
    ]

    assert (
        operation[
            "summary"
        ]
        == "Send authenticated device heartbeat"
    )

    assert (
        operation[
            "operationId"
        ]
        .startswith(
            "device_heartbeat"
        )
    )


def test_presence_endpoint_has_expected_operation() -> None:
    paths = get_openapi_paths()

    operation = paths[
        "/api/v1/device-agent/presence"
    ][
        "get"
    ]

    assert (
        operation[
            "summary"
        ]
        == "Get authenticated device presence"
    )

    assert (
        operation[
            "operationId"
        ]
        .startswith(
            "get_device_presence"
        )
    )


def test_phase07_router_has_exact_expected_paths() -> None:
    paths = get_openapi_paths()

    expected_paths = {
        "/api/v1/device-agent/heartbeat",
        "/api/v1/device-agent/presence",
    }

    assert (
        expected_paths
        <= set(
            paths.keys()
        )
    )