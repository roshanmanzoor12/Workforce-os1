from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


BACKEND_ROOT = Path(
    r"C:\workforce-os\backend"
)

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(BACKEND_ROOT),
    )


from app.config import settings
from app.main import app


EXPECTED_AUTH_ROUTES: dict[
    str,
    set[str],
] = {
    "/api/v1/auth/signup": {
        "post",
    },
    "/api/v1/auth/verify-email": {
        "post",
    },
    "/api/v1/auth/resend-verification": {
        "post",
    },
    "/api/v1/auth/login": {
        "post",
    },
    "/api/v1/auth/oauth/google/authorize": {
        "get",
    },
    "/api/v1/auth/oauth/google/callback": {
        "get",
    },
    "/api/v1/auth/refresh": {
        "post",
    },
    "/api/v1/auth/logout": {
        "post",
    },
    "/api/v1/auth/logout-all": {
        "post",
    },
    "/api/v1/auth/forgot-password": {
        "post",
    },
    "/api/v1/auth/verify-reset-otp": {
        "post",
    },
    "/api/v1/auth/reset-password": {
        "post",
    },
    "/api/v1/auth/me": {
        "get",
    },
    "/api/v1/auth/me/verified": {
        "get",
    },
    "/api/v1/auth/sessions": {
        "get",
    },
    "/api/v1/auth/sessions/{session_id}": {
        "delete",
    },
}


def separator(
    title: str,
) -> None:
    print()
    print(
        "=" * 72
    )
    print(
        f" {title}"
    )
    print(
        "=" * 72
    )
    print()


def get_openapi() -> dict[str, Any]:
    schema = app.openapi()

    if not isinstance(
        schema,
        dict,
    ):
        raise RuntimeError(
            "FastAPI openapi() did not return a dictionary."
        )

    return schema


def normalize_methods(
    path_item: dict[str, Any],
) -> set[str]:
    valid = {
        "get",
        "put",
        "post",
        "delete",
        "options",
        "head",
        "patch",
        "trace",
    }

    return {
        key.lower()
        for key in path_item
        if key.lower() in valid
    }


def verify_expected_routes(
    paths: dict[str, Any],
) -> bool:
    passed = True

    for path, expected_methods in (
        EXPECTED_AUTH_ROUTES.items()
    ):
        path_item = paths.get(
            path
        )

        if not isinstance(
            path_item,
            dict,
        ):
            print(
                f"MISSING  {path}"
            )

            passed = False
            continue

        actual_methods = normalize_methods(
            path_item
        )

        missing_methods = (
            expected_methods
            - actual_methods
        )

        if missing_methods:
            print(
                "MISSING  "
                f"{','.join(sorted(missing_methods)).upper():8} "
                f"{path}"
            )

            passed = False
            continue

        print(
            "PASS     "
            f"{','.join(sorted(expected_methods)).upper():8} "
            f"{path}"
        )

    return passed


def list_auth_paths(
    paths: dict[str, Any],
) -> None:
    auth_paths = [
        path
        for path in paths
        if "/auth/" in path
    ]

    if not auth_paths:
        print(
            "No auth paths found in OpenAPI."
        )

        return

    for path in sorted(
        auth_paths
    ):
        path_item = paths[
            path
        ]

        if not isinstance(
            path_item,
            dict,
        ):
            continue

        methods = normalize_methods(
            path_item
        )

        print(
            f"{','.join(sorted(methods)).upper():14} "
            f"{path}"
        )


def show_critical_request_schemas(
    paths: dict[str, Any],
) -> None:
    critical_paths = (
        "/api/v1/auth/signup",
        "/api/v1/auth/verify-email",
        "/api/v1/auth/forgot-password",
        "/api/v1/auth/verify-reset-otp",
        "/api/v1/auth/reset-password",
    )

    for path in critical_paths:
        path_item = paths.get(
            path
        )

        if not isinstance(
            path_item,
            dict,
        ):
            continue

        operation = (
            path_item.get(
                "post"
            )
        )

        if not isinstance(
            operation,
            dict,
        ):
            continue

        print(
            f"PATH: {path}"
        )

        print(
            "  operationId:",
            operation.get(
                "operationId"
            ),
        )

        request_body = (
            operation.get(
                "requestBody"
            )
        )

        if request_body is None:
            print(
                "  requestBody: <none>"
            )
        else:
            content = request_body.get(
                "content",
                {}
            )

            json_body = content.get(
                "application/json",
                {}
            )

            schema = json_body.get(
                "schema",
                {}
            )

            print(
                "  request schema:",
                json.dumps(
                    schema,
                    indent=2,
                ),
            )

        print()


def main() -> None:
    separator(
        "WorkforceOS Auth OpenAPI Runtime Verification"
    )

    print(
        "API prefix:",
        settings.api_v1_prefix,
    )

    print(
        "App title:",
        app.title,
    )

    schema = get_openapi()

    paths = schema.get(
        "paths"
    )

    if not isinstance(
        paths,
        dict,
    ):
        raise RuntimeError(
            "OpenAPI schema does not contain a valid paths object."
        )

    print(
        "OpenAPI total paths:",
        len(
            paths
        ),
    )

    separator(
        "AUTH PATHS EXPOSED BY FASTAPI"
    )

    list_auth_paths(
        paths
    )

    separator(
        "EXPECTED AUTH ROUTE CONTRACT"
    )

    contract_passed = (
        verify_expected_routes(
            paths
        )
    )

    separator(
        "CRITICAL OTP REQUEST SCHEMAS"
    )

    show_critical_request_schemas(
        paths
    )

    separator(
        "RESULT"
    )

    if not contract_passed:
        raise RuntimeError(
            "Auth OpenAPI contract is incomplete."
        )

    print(
        "PASS all expected WorkforceOS auth "
        "routes are exposed by FastAPI OpenAPI."
    )

    print()


if __name__ == "__main__":
    main()