from __future__ import annotations

import json
import os
import sys
import uuid
from dataclasses import dataclass
from typing import Any
from urllib import error, request


# =========================================================
# CONFIGURATION
# =========================================================

DEFAULT_API_BASE_URL = "http://127.0.0.1:8001"

API_BASE_URL = os.getenv(
    "WF_API_BASE_URL",
    DEFAULT_API_BASE_URL,
).rstrip("/")

ADMIN_TOKEN = os.getenv(
    "WF_ADMIN_TOKEN",
    "",
).strip()

WORKSPACE_ID = os.getenv(
    "WF_WORKSPACE_ID",
    "",
).strip()


# =========================================================
# ERRORS
# =========================================================


class SmokeTestError(RuntimeError):
    """Raised when a Phase 05 smoke-test step fails."""


# =========================================================
# DATA STRUCTURES
# =========================================================


@dataclass(frozen=True)
class RouteInfo:
    path: str
    method: str
    operation_id: str | None


@dataclass(frozen=True)
class HttpResponse:
    status_code: int
    payload: Any


# =========================================================
# DISPLAY HELPERS
# =========================================================


def print_heading(
    title: str,
) -> None:
    print()
    print(
        "=" * 64
    )
    print(
        title
    )
    print(
        "=" * 64
    )


def print_ok(
    message: str,
) -> None:
    print(
        f"[OK] {message}"
    )


def print_info(
    message: str,
) -> None:
    print(
        f"[INFO] {message}"
    )


def print_fail(
    message: str,
) -> None:
    print(
        f"[FAIL] {message}"
    )


def mask_secret(
    value: str,
) -> str:
    if len(value) <= 8:
        return "********"

    return (
        value[:4]
        + "..."
        + value[-4:]
    )


# =========================================================
# VALIDATION
# =========================================================


def require_environment() -> None:
    """
    Validate required smoke-test configuration.

    Authentication credentials are supplied by the caller through
    environment variables and are never hard-coded in this file.
    """

    if not ADMIN_TOKEN:
        raise SmokeTestError(
            "WF_ADMIN_TOKEN is required."
        )

    if not WORKSPACE_ID:
        raise SmokeTestError(
            "WF_WORKSPACE_ID is required."
        )

    try:
        uuid.UUID(
            WORKSPACE_ID
        )

    except ValueError as exc:
        raise SmokeTestError(
            "WF_WORKSPACE_ID must be a valid UUID."
        ) from exc


# =========================================================
# HTTP
# =========================================================


def build_headers(
    *,
    authenticated: bool = False,
    device_uuid: str | None = None,
    device_secret: str | None = None,
) -> dict[str, str]:
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    if authenticated:
        headers[
            "Authorization"
        ] = f"Bearer {ADMIN_TOKEN}"

    if device_uuid is not None:
        headers[
            "X-Device-UUID"
        ] = device_uuid

    if device_secret is not None:
        headers[
            "X-Device-Secret"
        ] = device_secret

    return headers


def http_json(
    *,
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> HttpResponse:
    body: bytes | None = None

    if payload is not None:
        body = json.dumps(
            payload
        ).encode(
            "utf-8"
        )

    http_request = request.Request(
        url=url,
        data=body,
        headers=headers or {},
        method=method.upper(),
    )

    try:
        with request.urlopen(
            http_request,
            timeout=30,
        ) as response:
            raw = response.read()

            parsed: Any = None

            if raw:
                parsed = json.loads(
                    raw.decode(
                        "utf-8"
                    )
                )

            return HttpResponse(
                status_code=response.status,
                payload=parsed,
            )

    except error.HTTPError as exc:
        raw = exc.read()

        parsed: Any

        try:
            parsed = json.loads(
                raw.decode(
                    "utf-8"
                )
            )

        except Exception:
            parsed = raw.decode(
                "utf-8",
                errors="replace",
            )

        return HttpResponse(
            status_code=exc.code,
            payload=parsed,
        )

    except error.URLError as exc:
        raise SmokeTestError(
            f"Could not reach API at {url}: {exc}"
        ) from exc


# =========================================================
# OPENAPI DISCOVERY
# =========================================================


def load_openapi() -> dict[str, Any]:
    response = http_json(
        method="GET",
        url=f"{API_BASE_URL}/openapi.json",
        headers={
            "Accept": "application/json",
        },
    )

    if response.status_code != 200:
        raise SmokeTestError(
            "Unable to load OpenAPI document. "
            f"HTTP {response.status_code}: "
            f"{response.payload!r}"
        )

    if not isinstance(
        response.payload,
        dict,
    ):
        raise SmokeTestError(
            "OpenAPI response is not a JSON object."
        )

    return response.payload


def iter_routes(
    openapi: dict[str, Any],
) -> list[RouteInfo]:
    result: list[RouteInfo] = []

    paths = openapi.get(
        "paths",
        {},
    )

    if not isinstance(
        paths,
        dict,
    ):
        return result

    for path, operations in paths.items():
        if not isinstance(
            operations,
            dict,
        ):
            continue

        for method, operation in operations.items():
            if method.lower() not in {
                "get",
                "post",
                "put",
                "patch",
                "delete",
            }:
                continue

            operation_id: str | None = None

            if isinstance(
                operation,
                dict,
            ):
                value = operation.get(
                    "operationId"
                )

                if isinstance(
                    value,
                    str,
                ):
                    operation_id = value

            result.append(
                RouteInfo(
                    path=path,
                    method=method.upper(),
                    operation_id=operation_id,
                )
            )

    return result


def route_search_text(
    route: RouteInfo,
) -> str:
    return (
        f"{route.path} "
        f"{route.operation_id or ''}"
    ).lower()


def discover_activation_create_route(
    routes: list[RouteInfo],
) -> RouteInfo:
    candidates = [
        route
        for route in routes
        if (
            route.method == "POST"
            and "activation" in route_search_text(
                route
            )
            and "{workspace_id}" in route.path
            and "revoke" not in route_search_text(
                route
            )
        )
    ]

    if len(
        candidates
    ) != 1:
        matches = [
            f"{route.method} {route.path}"
            for route in candidates
        ]

        raise SmokeTestError(
            "Could not uniquely discover activation-code "
            f"creation route. Matches: {matches}"
        )

    return candidates[0]


def discover_registration_route(
    routes: list[RouteInfo],
) -> RouteInfo:
    candidates = [
        route
        for route in routes
        if (
            route.method == "POST"
            and (
                "device-registration"
                in route_search_text(
                    route
                )
                or (
                    "registration"
                    in route_search_text(
                        route
                    )
                    and "register"
                    in route_search_text(
                        route
                    )
                )
            )
        )
    ]

    candidates = [
        route
        for route in candidates
        if "{workspace_id}" not in route.path
    ]

    if len(
        candidates
    ) != 1:
        matches = [
            f"{route.method} {route.path}"
            for route in candidates
        ]

        raise SmokeTestError(
            "Could not uniquely discover public device "
            f"registration route. Matches: {matches}"
        )

    return candidates[0]


def discover_agent_me_route(
    routes: list[RouteInfo],
) -> RouteInfo:
    candidates = [
        route
        for route in routes
        if (
            route.method == "GET"
            and (
                "device-agent"
                in route_search_text(
                    route
                )
                or "agent" in route_search_text(
                    route
                )
            )
            and (
                route.path.endswith(
                    "/me"
                )
                or "_me" in (
                    route.operation_id or ""
                ).lower()
            )
        )
    ]

    if len(
        candidates
    ) != 1:
        matches = [
            f"{route.method} {route.path}"
            for route in candidates
        ]

        raise SmokeTestError(
            "Could not uniquely discover device-agent "
            f"identity route. Matches: {matches}"
        )

    return candidates[0]


# =========================================================
# RESPONSE EXTRACTION
# =========================================================


def find_string_by_keys(
    value: Any,
    keys: tuple[str, ...],
) -> str | None:
    """
    Recursively locate a string response field.

    Keys are checked in priority order.
    """

    if isinstance(
        value,
        dict,
    ):
        for key in keys:
            candidate = value.get(
                key
            )

            if isinstance(
                candidate,
                str,
            ) and candidate:
                return candidate

        for nested in value.values():
            result = find_string_by_keys(
                nested,
                keys,
            )

            if result is not None:
                return result

    elif isinstance(
        value,
        list,
    ):
        for nested in value:
            result = find_string_by_keys(
                nested,
                keys,
            )

            if result is not None:
                return result

    return None


def extract_activation_code(
    payload: Any,
) -> str:
    activation_code = find_string_by_keys(
        payload,
        (
            "activation_code",
            "plaintext_code",
            "code",
        ),
    )

    if activation_code is None:
        raise SmokeTestError(
            "Activation-code creation succeeded, but a "
            "plaintext activation code could not be found "
            "in the response."
        )

    return activation_code


def extract_device_uuid(
    payload: Any,
) -> str:
    device_uuid = find_string_by_keys(
        payload,
        (
            "device_uuid",
        ),
    )

    if device_uuid is None:
        raise SmokeTestError(
            "Registration succeeded, but device_uuid "
            "was not present in the response."
        )

    try:
        uuid.UUID(
            device_uuid
        )

    except ValueError as exc:
        raise SmokeTestError(
            "Registration returned an invalid device_uuid."
        ) from exc

    return device_uuid


def extract_device_secret(
    payload: Any,
) -> str:
    device_secret = find_string_by_keys(
        payload,
        (
            "device_secret",
            "plaintext_secret",
            "secret",
        ),
    )

    if device_secret is None:
        raise SmokeTestError(
            "Registration succeeded, but the one-time "
            "device secret was not present in the response."
        )

    if len(
        device_secret
    ) < 20:
        raise SmokeTestError(
            "Registration returned a device secret shorter "
            "than the expected minimum length."
        )

    return device_secret


# =========================================================
# URL HELPERS
# =========================================================


def resolve_route_url(
    route: RouteInfo,
) -> str:
    path = route.path.replace(
        "{workspace_id}",
        WORKSPACE_ID,
    )

    return (
        f"{API_BASE_URL}{path}"
    )


# =========================================================
# ACTIVATION CODE
# =========================================================


def create_activation_code(
    route: RouteInfo,
) -> str:
    print_heading(
        "1. CREATE DEVICE ACTIVATION CODE"
    )

    print_info(
        f"Route: {route.method} {route.path}"
    )

    payload = {
        "label": (
            "Phase 05 registration smoke test"
        ),
        "max_uses": 1,
    }

    response = http_json(
        method=route.method,
        url=resolve_route_url(
            route
        ),
        payload=payload,
        headers=build_headers(
            authenticated=True
        ),
    )

    if response.status_code not in {
        200,
        201,
    }:
        raise SmokeTestError(
            "Activation-code creation failed. "
            f"HTTP {response.status_code}: "
            f"{response.payload!r}"
        )

    activation_code = (
        extract_activation_code(
            response.payload
        )
    )

    print_ok(
        "Activation code created."
    )

    print_info(
        "Activation code: "
        f"{mask_secret(activation_code)}"
    )

    return activation_code


# =========================================================
# DEVICE REGISTRATION
# =========================================================


def register_device(
    route: RouteInfo,
    *,
    activation_code: str,
) -> tuple[str, str]:
    print_heading(
        "2. REGISTER DEVICE"
    )

    print_info(
        f"Route: {route.method} {route.path}"
    )

    unique_suffix = (
        uuid.uuid4().hex[:12]
    )

    payload = {
        "activation_code": activation_code,
        "hostname": (
            f"WF-PHASE05-{unique_suffix}"
        ),
        "os_name": "Windows",
        "os_version": "11",
        "architecture": "x64",
        "agent_version": "0.5.0-smoke",
        "agent_identifier": (
            f"phase05-smoke-{unique_suffix}"
        ),
    }

    response = http_json(
        method=route.method,
        url=resolve_route_url(
            route
        ),
        payload=payload,
        headers=build_headers(),
    )

    if response.status_code not in {
        200,
        201,
    }:
        raise SmokeTestError(
            "Device registration failed. "
            f"HTTP {response.status_code}: "
            f"{response.payload!r}"
        )

    device_uuid = (
        extract_device_uuid(
            response.payload
        )
    )

    device_secret = (
        extract_device_secret(
            response.payload
        )
    )

    print_ok(
        "Device registration succeeded."
    )

    print_info(
        f"Device UUID: {device_uuid}"
    )

    print_info(
        "Device secret: "
        f"{mask_secret(device_secret)}"
    )

    return (
        device_uuid,
        device_secret,
    )


# =========================================================
# DEVICE AUTHENTICATION
# =========================================================


def authenticate_device(
    route: RouteInfo,
    *,
    device_uuid: str,
    device_secret: str,
) -> None:
    print_heading(
        "3. AUTHENTICATE DEVICE"
    )

    print_info(
        f"Route: {route.method} {route.path}"
    )

    response = http_json(
        method=route.method,
        url=resolve_route_url(
            route
        ),
        headers=build_headers(
            device_uuid=device_uuid,
            device_secret=device_secret,
        ),
    )

    if response.status_code != 200:
        raise SmokeTestError(
            "Device-agent authentication failed. "
            f"HTTP {response.status_code}: "
            f"{response.payload!r}"
        )

    authenticated = None

    if isinstance(
        response.payload,
        dict,
    ):
        authenticated = (
            response.payload.get(
                "authenticated"
            )
        )

    if authenticated is False:
        raise SmokeTestError(
            "Device-agent endpoint returned "
            "authenticated=false."
        )

    returned_uuid = find_string_by_keys(
        response.payload,
        (
            "device_uuid",
        ),
    )

    if (
        returned_uuid is not None
        and returned_uuid != device_uuid
    ):
        raise SmokeTestError(
            "Authenticated device UUID does not match "
            "the registered device UUID."
        )

    print_ok(
        "Device authentication succeeded."
    )

    print_info(
        f"Authenticated device: {device_uuid}"
    )


# =========================================================
# MAIN
# =========================================================


def main() -> int:
    try:
        require_environment()

        print_heading(
            "WORKFORCEOS PHASE 05 DEVICE REGISTRATION SMOKE TEST"
        )

        print_info(
            f"API: {API_BASE_URL}"
        )

        print_info(
            f"Workspace: {WORKSPACE_ID}"
        )

        openapi = load_openapi()

        routes = iter_routes(
            openapi
        )

        activation_route = (
            discover_activation_create_route(
                routes
            )
        )

        registration_route = (
            discover_registration_route(
                routes
            )
        )

        agent_me_route = (
            discover_agent_me_route(
                routes
            )
        )

        print_heading(
            "DISCOVERED ROUTES"
        )

        print_info(
            f"Activation: "
            f"{activation_route.method} "
            f"{activation_route.path}"
        )

        print_info(
            f"Registration: "
            f"{registration_route.method} "
            f"{registration_route.path}"
        )

        print_info(
            f"Agent auth: "
            f"{agent_me_route.method} "
            f"{agent_me_route.path}"
        )

        activation_code = (
            create_activation_code(
                activation_route
            )
        )

        (
            device_uuid,
            device_secret,
        ) = register_device(
            registration_route,
            activation_code=activation_code,
        )

        authenticate_device(
            agent_me_route,
            device_uuid=device_uuid,
            device_secret=device_secret,
        )

        print_heading(
            "PHASE 05 SMOKE RESULT"
        )

        print_ok(
            "Activation code creation passed."
        )

        print_ok(
            "Device registration passed."
        )

        print_ok(
            "One-time credential issuance passed."
        )

        print_ok(
            "Control-to-tenant device routing passed."
        )

        print_ok(
            "Device-agent authentication passed."
        )

        print()
        print(
            "PHASE 05 REGISTRATION SMOKE TEST: PASS"
        )

        return 0

    except SmokeTestError as exc:
        print_heading(
            "PHASE 05 SMOKE RESULT"
        )

        print_fail(
            str(
                exc
            )
        )

        print()
        print(
            "PHASE 05 REGISTRATION SMOKE TEST: FAIL"
        )

        return 1

    except KeyboardInterrupt:
        print()
        print_fail(
            "Smoke test interrupted."
        )

        return 130


if __name__ == "__main__":
    sys.exit(
        main()
    )