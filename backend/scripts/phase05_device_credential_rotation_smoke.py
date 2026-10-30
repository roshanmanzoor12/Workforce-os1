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

API_BASE_URL = os.getenv(
    "WF_API_BASE_URL",
    "http://127.0.0.1:8001",
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
    """Raised when credential rotation smoke validation fails."""


# =========================================================
# RESPONSE TYPES
# =========================================================


@dataclass(frozen=True)
class HttpResponse:
    status_code: int
    payload: Any


@dataclass(frozen=True)
class RegisteredDevice:
    device_id: str
    device_uuid: str
    device_secret: str


# =========================================================
# DISPLAY HELPERS
# =========================================================


def heading(
    title: str,
) -> None:
    print()
    print("=" * 64)
    print(title)
    print("=" * 64)


def ok(
    message: str,
) -> None:
    print(f"[OK] {message}")


def info(
    message: str,
) -> None:
    print(f"[INFO] {message}")


def fail(
    message: str,
) -> None:
    print(f"[FAIL] {message}")


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
# ENVIRONMENT VALIDATION
# =========================================================


def require_environment() -> None:
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

    req = request.Request(
        url=url,
        data=body,
        headers=headers or {},
        method=method.upper(),
    )

    try:
        with request.urlopen(
            req,
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
            f"Could not reach API: {exc}"
        ) from exc


def admin_headers() -> dict[str, str]:
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": (
            f"Bearer {ADMIN_TOKEN}"
        ),
    }


def agent_headers(
    *,
    device_uuid: str,
    device_secret: str,
) -> dict[str, str]:
    return {
        "Accept": "application/json",
        "X-Device-UUID": device_uuid,
        "X-Device-Secret": device_secret,
    }


# =========================================================
# RESPONSE EXTRACTION
# =========================================================


def find_string(
    value: Any,
    keys: tuple[str, ...],
) -> str | None:
    if isinstance(
        value,
        dict,
    ):
        for key in keys:
            candidate = value.get(
                key
            )

            if (
                isinstance(
                    candidate,
                    str,
                )
                and candidate
            ):
                return candidate

        for nested in value.values():
            result = find_string(
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
            result = find_string(
                nested,
                keys,
            )

            if result is not None:
                return result

    return None


def extract_registered_device(
    payload: Any,
) -> RegisteredDevice:
    if not isinstance(
        payload,
        dict,
    ):
        raise SmokeTestError(
            "Registration response is not a JSON object."
        )

    device_payload = payload.get(
        "device"
    )

    credential_payload = payload.get(
        "credential"
    )

    if not isinstance(
        device_payload,
        dict,
    ):
        raise SmokeTestError(
            "Registration response does not contain "
            "a valid device object."
        )

    if not isinstance(
        credential_payload,
        dict,
    ):
        raise SmokeTestError(
            "Registration response does not contain "
            "a valid credential object."
        )

    device_id = device_payload.get(
        "id"
    )

    device_uuid = device_payload.get(
        "device_uuid"
    )

    device_secret = (
        credential_payload.get(
            "device_secret"
        )
        or credential_payload.get(
            "plaintext_secret"
        )
        or credential_payload.get(
            "secret"
        )
    )

    if not isinstance(
        device_id,
        str,
    ):
        raise SmokeTestError(
            "Tenant device id missing from "
            "registration response."
        )

    if not isinstance(
        device_uuid,
        str,
    ):
        raise SmokeTestError(
            "device_uuid missing from "
            "registration response."
        )

    if not isinstance(
        device_secret,
        str,
    ):
        raise SmokeTestError(
            "device_secret missing from "
            "registration response."
        )

    try:
        uuid.UUID(
            device_id
        )

    except ValueError as exc:
        raise SmokeTestError(
            "Registration returned invalid tenant device id."
        ) from exc

    try:
        uuid.UUID(
            device_uuid
        )

    except ValueError as exc:
        raise SmokeTestError(
            "Registration returned invalid device_uuid."
        ) from exc

    return RegisteredDevice(
        device_id=device_id,
        device_uuid=device_uuid,
        device_secret=device_secret,
    )


# =========================================================
# ACTIVATION CODE
# =========================================================


def create_activation_code() -> str:
    heading(
        "1. CREATE ACTIVATION CODE"
    )

    response = http_json(
        method="POST",
        url=(
            f"{API_BASE_URL}"
            f"/api/v1/workspaces/"
            f"{WORKSPACE_ID}/"
            f"device-activation-codes"
        ),
        payload={
            "label": (
                "Phase 05 credential rotation smoke"
            ),
            "max_uses": 1,
        },
        headers=admin_headers(),
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

    activation_code = find_string(
        response.payload,
        (
            "activation_code",
            "plaintext_code",
            "code",
        ),
    )

    if activation_code is None:
        raise SmokeTestError(
            "Activation code not found in response."
        )

    ok(
        "Activation code created."
    )

    info(
        "Activation code: "
        f"{mask_secret(activation_code)}"
    )

    return activation_code


# =========================================================
# DEVICE REGISTRATION
# =========================================================


def register_device(
    activation_code: str,
) -> RegisteredDevice:
    heading(
        "2. REGISTER TEST DEVICE"
    )

    suffix = (
        uuid.uuid4().hex[:12]
    )

    response = http_json(
        method="POST",
        url=(
            f"{API_BASE_URL}"
            f"/api/v1/device-registration/register"
        ),
        payload={
            "activation_code": activation_code,
            "hostname": (
                f"WF-ROTATE-{suffix}"
            ),
            "os_name": "Windows",
            "os_version": "11",
            "architecture": "x64",
            "agent_version": (
                "0.5.0-rotation-smoke"
            ),
            "agent_identifier": (
                f"phase05-rotation-{suffix}"
            ),
        },
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
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

    registered = extract_registered_device(
        response.payload
    )

    ok(
        "Device registered."
    )

    info(
        f"Tenant Device ID: {registered.device_id}"
    )

    info(
        f"Device UUID: {registered.device_uuid}"
    )

    info(
        "Original secret: "
        f"{mask_secret(registered.device_secret)}"
    )

    return registered


# =========================================================
# DEVICE AUTHENTICATION
# =========================================================


def authenticate(
    *,
    device_uuid: str,
    device_secret: str,
) -> HttpResponse:
    return http_json(
        method="GET",
        url=(
            f"{API_BASE_URL}"
            f"/api/v1/device-agent/me"
        ),
        headers=agent_headers(
            device_uuid=device_uuid,
            device_secret=device_secret,
        ),
    )


def verify_original_credential(
    *,
    device_uuid: str,
    device_secret: str,
) -> None:
    heading(
        "3. VERIFY ORIGINAL CREDENTIAL"
    )

    response = authenticate(
        device_uuid=device_uuid,
        device_secret=device_secret,
    )

    if response.status_code != 200:
        raise SmokeTestError(
            "Original credential failed before rotation. "
            f"HTTP {response.status_code}: "
            f"{response.payload!r}"
        )

    ok(
        "Original credential authenticates."
    )


# =========================================================
# OPENAPI ROTATION ROUTE
# =========================================================


def discover_rotation_route(
    *,
    device_id: str,
    device_uuid: str,
) -> str:
    response = http_json(
        method="GET",
        url=(
            f"{API_BASE_URL}"
            f"/openapi.json"
        ),
        headers={
            "Accept": "application/json",
        },
    )

    if response.status_code != 200:
        raise SmokeTestError(
            "Could not load OpenAPI document."
        )

    if not isinstance(
        response.payload,
        dict,
    ):
        raise SmokeTestError(
            "Invalid OpenAPI response."
        )

    paths = response.payload.get(
        "paths",
        {},
    )

    if not isinstance(
        paths,
        dict,
    ):
        raise SmokeTestError(
            "OpenAPI paths are missing."
        )

    matches: list[str] = []

    for path, operations in paths.items():
        if not isinstance(
            operations,
            dict,
        ):
            continue

        lowered = path.lower()

        if "credential" not in lowered:
            continue

        if "rotate" not in lowered:
            continue

        if "post" not in operations:
            continue

        if "{workspace_id}" not in path:
            continue

        matches.append(
            path
        )

    if len(matches) != 1:
        raise SmokeTestError(
            "Could not uniquely discover credential "
            f"rotation route. Matches: {matches}"
        )

    route = matches[0]

    route = route.replace(
        "{workspace_id}",
        WORKSPACE_ID,
    )

    route = route.replace(
        "{device_id}",
        device_id,
    )

    route = route.replace(
        "{device_uuid}",
        device_uuid,
    )

    if "{" in route or "}" in route:
        raise SmokeTestError(
            "Rotation route still contains unresolved "
            f"path parameters: {route}"
        )

    return route


# =========================================================
# CREDENTIAL ROTATION
# =========================================================


def rotate_credential(
    *,
    device_id: str,
    device_uuid: str,
) -> str:
    heading(
        "4. ROTATE DEVICE CREDENTIAL"
    )

    route = discover_rotation_route(
        device_id=device_id,
        device_uuid=device_uuid,
    )

    info(
        f"Rotation route: POST {route}"
    )

    response = http_json(
        method="POST",
        url=(
            f"{API_BASE_URL}{route}"
        ),
        payload={},
        headers=admin_headers(),
    )

    if response.status_code not in {
        200,
        201,
    }:
        raise SmokeTestError(
            "Credential rotation failed. "
            f"HTTP {response.status_code}: "
            f"{response.payload!r}"
        )

    new_secret = find_string(
        response.payload,
        (
            "device_secret",
            "plaintext_secret",
            "secret",
        ),
    )

    if new_secret is None:
        raise SmokeTestError(
            "New device secret missing from "
            "rotation response."
        )

    ok(
        "Credential rotated."
    )

    info(
        "New secret: "
        f"{mask_secret(new_secret)}"
    )

    return new_secret


# =========================================================
# POST-ROTATION VALIDATION
# =========================================================


def verify_new_secret(
    *,
    device_uuid: str,
    new_secret: str,
) -> None:
    heading(
        "5. VERIFY NEW SECRET"
    )

    response = authenticate(
        device_uuid=device_uuid,
        device_secret=new_secret,
    )

    if response.status_code != 200:
        raise SmokeTestError(
            "New credential authentication failed. "
            f"HTTP {response.status_code}: "
            f"{response.payload!r}"
        )

    ok(
        "New credential authenticates."
    )


def verify_old_secret_rejected(
    *,
    device_uuid: str,
    old_secret: str,
) -> None:
    heading(
        "6. VERIFY OLD SECRET IS REJECTED"
    )

    response = authenticate(
        device_uuid=device_uuid,
        device_secret=old_secret,
    )

    if response.status_code == 200:
        raise SmokeTestError(
            "Old credential still authenticates "
            "after rotation."
        )

    if response.status_code != 401:
        raise SmokeTestError(
            "Old credential was rejected, but "
            "HTTP 401 was expected. "
            f"Received HTTP {response.status_code}: "
            f"{response.payload!r}"
        )

    ok(
        "Old credential rejected with HTTP 401."
    )


# =========================================================
# MAIN
# =========================================================


def main() -> int:
    try:
        require_environment()

        heading(
            "WORKFORCEOS PHASE 05 "
            "CREDENTIAL ROTATION SMOKE TEST"
        )

        info(
            f"API: {API_BASE_URL}"
        )

        info(
            f"Workspace: {WORKSPACE_ID}"
        )

        activation_code = (
            create_activation_code()
        )

        registered = register_device(
            activation_code
        )

        verify_original_credential(
            device_uuid=registered.device_uuid,
            device_secret=registered.device_secret,
        )

        new_secret = rotate_credential(
            device_id=registered.device_id,
            device_uuid=registered.device_uuid,
        )

        verify_new_secret(
            device_uuid=registered.device_uuid,
            new_secret=new_secret,
        )

        verify_old_secret_rejected(
            device_uuid=registered.device_uuid,
            old_secret=registered.device_secret,
        )

        heading(
            "PHASE 05 ROTATION RESULT"
        )

        ok(
            "Original credential authentication passed."
        )

        ok(
            "Credential rotation passed."
        )

        ok(
            "New credential authentication passed."
        )

        ok(
            "Old credential rejection passed."
        )

        print()
        print(
            "PHASE 05 CREDENTIAL ROTATION "
            "SMOKE TEST: PASS"
        )

        return 0

    except SmokeTestError as exc:
        heading(
            "PHASE 05 ROTATION RESULT"
        )

        fail(
            str(exc)
        )

        print()
        print(
            "PHASE 05 CREDENTIAL ROTATION "
            "SMOKE TEST: FAIL"
        )

        return 1

    except KeyboardInterrupt:
        print()
        fail(
            "Smoke test interrupted."
        )

        return 130


if __name__ == "__main__":
    sys.exit(
        main()
    )