from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from fastapi import FastAPI
from fastapi import routing as fastapi_routing
from fastapi.routing import APIRoute

from app.modules.workspace_rbac.scope_router import router


def iter_registered_api_routes(
    routes: Any,
) -> Iterator[Any]:
    """
    Inspect effective API routes, including router prefixes.

    Supports newer FastAPI route contexts and older flat routes.
    """
    public_iterator = getattr(
        fastapi_routing,
        "iter_route_contexts",
        None,
    )

    if callable(public_iterator):
        for context in public_iterator(routes):
            original = getattr(
                context,
                "original_route",
                None,
            )

            if isinstance(original, APIRoute):
                yield context

        return

    for route in routes:
        if isinstance(route, APIRoute):
            yield route
            continue

        # Compatibility with FastAPI versions that expose included
        # router contexts before exposing the public iterator.
        effective_contexts = getattr(
            route,
            "effective_route_contexts",
            None,
        )

        if not callable(effective_contexts):
            continue

        for context in effective_contexts():
            original = getattr(
                context,
                "original_route",
                None,
            )

            if isinstance(original, APIRoute):
                yield context


def register_membership_scope_routes(
    app: FastAPI,
    *,
    prefix: str,
) -> None:
    if prefix and (
        not prefix.startswith("/")
        or prefix.endswith("/")
    ):
        raise ValueError(
            "Scope API prefix must start with '/' "
            "and must not end with '/'."
        )

    expected = [
        (
            prefix + route.path,
            method,
            route.endpoint,
        )
        for route in iter_registered_api_routes(router.routes)
        for method in sorted(route.methods or ())
    ]

    if not expected:
        raise RuntimeError(
            "The membership scope router contains no API operations."
        )

    installed_routes = tuple(
        iter_registered_api_routes(app.routes)
    )
    installed_count = 0

    for path, method, endpoint in expected:
        matches = [
            route
            for route in installed_routes
            if route.path == path
            and method in (route.methods or ())
        ]

        if not matches:
            continue

        if (
            len(matches) != 1
            or matches[0].endpoint is not endpoint
        ):
            raise RuntimeError(
                "Conflicting membership scope route: "
                f"{method} {path}"
            )

        installed_count += 1

    if installed_count == len(expected):
        return

    if installed_count:
        raise RuntimeError(
            "Membership scope routes are partially registered."
        )

    app.include_router(
        router,
        prefix=prefix,
    )

    # Discard any schema generated before these routes were added.
    app.openapi_schema = None


__all__ = [
    "iter_registered_api_routes",
    "register_membership_scope_routes",
]