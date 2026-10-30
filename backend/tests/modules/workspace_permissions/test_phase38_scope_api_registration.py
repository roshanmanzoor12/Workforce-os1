from __future__ import annotations

import importlib

import pytest
from fastapi import APIRouter, FastAPI

from app.modules.workspace_rbac.scope_api_contract import (
    SCOPE_API_CONTRACT,
)
from app.modules.workspace_rbac.scope_registration import (
    iter_registered_api_routes,
    register_membership_scope_routes,
)
from app.modules.workspace_rbac.scope_router import (
    router as scope_router,
)


PREFIX = "/api/v1"


def route_matches(
    app: FastAPI,
    method: str,
    path: str,
) -> list:
    return [
        route
        for route in iter_registered_api_routes(app.routes)
        if route.path == path
        and method in (route.methods or ())
    ]


def test_registration_installs_each_operation_once() -> None:
    app = FastAPI()

    register_membership_scope_routes(
        app,
        prefix=PREFIX,
    )
    register_membership_scope_routes(
        app,
        prefix=PREFIX,
    )

    schema = app.openapi()

    for method, suffix in SCOPE_API_CONTRACT:
        path = PREFIX + suffix
        matches = route_matches(app, method, path)

        assert len(matches) == 1
        assert (
            matches[0].endpoint.__module__
            == "app.modules.workspace_rbac.scope_router"
        )
        assert method.lower() in schema["paths"][path]


def test_registration_rejects_conflicting_route() -> None:
    app = FastAPI()

    get_suffix = next(
        suffix
        for method, suffix in SCOPE_API_CONTRACT
        if method == "GET"
    )

    async def conflicting_endpoint() -> dict[str, bool]:
        return {"conflict": True}

    app.add_api_route(
        PREFIX + get_suffix,
        conflicting_endpoint,
        methods=["GET"],
    )

    with pytest.raises(RuntimeError, match="Conflicting"):
        register_membership_scope_routes(
            app,
            prefix=PREFIX,
        )


def test_registration_rejects_partial_registration() -> None:
    app = FastAPI()

    get_route = next(
        route
        for route in iter_registered_api_routes(
            scope_router.routes
        )
        if "GET" in (route.methods or ())
    )

    app.add_api_route(
        PREFIX + get_route.path,
        get_route.endpoint,
        methods=["GET"],
    )

    with pytest.raises(RuntimeError, match="partially"):
        register_membership_scope_routes(
            app,
            prefix=PREFIX,
        )


def test_real_application_contains_scope_operations() -> None:
    main = importlib.import_module("app.main")
    app = main.app

    installed = tuple(
        iter_registered_api_routes(app.routes)
    )

    for method, suffix in SCOPE_API_CONTRACT:
        matches = [
            route
            for route in installed
            if isinstance(route.path, str)
            and route.path.endswith(suffix)
            and method in (route.methods or ())
        ]

        assert len(matches) == 1, (
            f"Expected one installed route for "
            f"{method} {suffix}; found {len(matches)}."
        )
        assert (
            matches[0].endpoint.__module__
            == "app.modules.workspace_rbac.scope_router"
        )


def test_registration_rejects_conflict_in_included_router() -> None:
    app = FastAPI()
    other_router = APIRouter()

    get_suffix = next(
        suffix
        for method, suffix in SCOPE_API_CONTRACT
        if method == "GET"
    )

    async def conflicting_endpoint() -> dict[str, bool]:
        return {"conflict": True}

    other_router.add_api_route(
        get_suffix,
        conflicting_endpoint,
        methods=["GET"],
    )
    app.include_router(other_router, prefix=PREFIX)

    with pytest.raises(RuntimeError, match="Conflicting"):
        register_membership_scope_routes(
            app,
            prefix=PREFIX,
        )


def test_registration_rejects_duplicate_inclusions() -> None:
    app = FastAPI()

    app.include_router(scope_router, prefix=PREFIX)
    app.include_router(scope_router, prefix=PREFIX)

    with pytest.raises(RuntimeError, match="Conflicting"):
        register_membership_scope_routes(
            app,
            prefix=PREFIX,
        )


def test_registration_refreshes_existing_openapi_schema() -> None:
    app = FastAPI()
    previous_schema = app.openapi()

    assert previous_schema["paths"] == {}

    register_membership_scope_routes(
        app,
        prefix=PREFIX,
    )

    updated_schema = app.openapi()

    for method, suffix in SCOPE_API_CONTRACT:
        assert (
            method.lower()
            in updated_schema["paths"][PREFIX + suffix]
        )