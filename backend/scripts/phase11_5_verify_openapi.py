from __future__ import annotations

import sys
from pathlib import Path


BACKEND_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

backend_root_text = str(
    BACKEND_ROOT
)

if backend_root_text not in sys.path:
    sys.path.insert(
        0,
        backend_root_text,
    )


from app.main import app  # noqa: E402


EXPECTED = {
    "/api/v1/billing/plans": {
        "get",
    },
    "/api/v1/billing/subscription": {
        "get",
    },
    "/api/v1/billing/entitlements": {
        "get",
    },
    "/api/v1/billing/workspace-access": {
        "get",
    },
    "/api/v1/workspaces": {
        "post",
    },
}


def main() -> None:
    schema = app.openapi()

    paths = schema.get(
        "paths",
        {},
    )

    for path, methods in EXPECTED.items():
        if path not in paths:
            raise RuntimeError(
                f"Missing OpenAPI path: {path}"
            )

        actual_methods = {
            method.lower()
            for method
            in paths[path].keys()
        }

        for method in methods:
            if method not in actual_methods:
                raise RuntimeError(
                    "Missing OpenAPI operation: "
                    f"{method.upper()} {path}"
                )

            print(
                "PASS:",
                method.upper(),
                path,
            )

    billing_text = str(
        {
            path: definition
            for path, definition
            in paths.items()
            if "/billing/" in path
        }
    ).lower()

    forbidden = (
        "card_number",
        "cardnumber",
        "cvv",
        "cvc",
        "security_code",
    )

    for word in forbidden:
        if word in billing_text:
            raise RuntimeError(
                "Raw payment field exposed "
                f"in OpenAPI: {word}"
            )

    print(
        "PASS billing OpenAPI privacy"
    )


if __name__ == "__main__":
    main()