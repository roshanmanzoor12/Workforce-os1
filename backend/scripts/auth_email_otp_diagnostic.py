from __future__ import annotations

import sys
from pathlib import Path


BACKEND_ROOT = Path(
    r"C:\workforce-os\backend"
)

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(BACKEND_ROOT),
    )


from fastapi.routing import APIRoute

from app.config import settings
from app.main import app


ENV_FILE = Path(
    r"C:\workforce-os\.env"
)


def mask(
    value: object | None,
) -> str:
    if value is None:
        return "<missing>"

    text = str(
        value
    )

    if not text:
        return "<empty>"

    if len(text) <= 6:
        return "***"

    return (
        f"{text[:2]}***{text[-2:]}"
    )


def load_env_keys() -> set[str]:
    keys: set[str] = set()

    if not ENV_FILE.exists():
        return keys

    for raw_line in ENV_FILE.read_text(
        encoding="utf-8-sig",
    ).splitlines():
        line = raw_line.strip()

        if (
            not line
            or line.startswith("#")
            or "=" not in line
        ):
            continue

        key, _ = line.split(
            "=",
            1,
        )

        keys.add(
            key.strip()
        )

    return keys


def get_setting(
    name: str,
) -> object | None:
    return getattr(
        settings,
        name,
        None,
    )


def print_setting_status(
    name: str,
    *,
    secret: bool = False,
) -> None:
    value = get_setting(
        name
    )

    if secret:
        display = mask(
            value
        )
    else:
        display = (
            "<configured>"
            if value not in (
                None,
                "",
            )
            else "<missing>"
        )

    print(
        f"{name}: {display}"
    )


def list_auth_routes() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []

    for route in app.routes:
        if not isinstance(
            route,
            APIRoute,
        ):
            continue

        if "/auth/" not in route.path:
            continue

        rows.append(
            {
                "path": route.path,
                "methods": sorted(
                    route.methods
                    or []
                ),
                "name": route.name,
            }
        )

    return rows


def main() -> None:
    print()
    print(
        "================================================="
    )
    print(
        " WorkforceOS Auth / Email / OTP Diagnostic"
    )
    print(
        "================================================="
    )
    print()

    env_keys = load_env_keys()

    print(
        "[1/5] Environment keys"
    )
    print()

    required_env = [
        "EMAIL_ENABLED",
        "SMTP_HOST",
        "SMTP_PORT",
        "SMTP_USERNAME",
        "SMTP_PASSWORD",
        "SMTP_FROM_EMAIL",
        "SMTP_USE_TLS",
        "EMAIL_VERIFICATION_OTP_MINUTES",
        "PASSWORD_RESET_OTP_MINUTES",
        "OTP_LENGTH",
        "OTP_MAX_ATTEMPTS",
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET",
        "GOOGLE_REDIRECT_URI",
    ]

    missing_keys = [
        key
        for key in required_env
        if key not in env_keys
    ]

    if missing_keys:
        print(
            "Missing .env keys:"
        )

        for key in missing_keys:
            print(
                f"  - {key}"
            )
    else:
        print(
            "PASS required .env keys exist"
        )

    print()
    print(
        "[2/5] Loaded application settings"
    )
    print()

    for name in (
        "email_enabled",
        "smtp_host",
        "smtp_port",
        "smtp_username",
        "smtp_from_email",
        "smtp_use_tls",
        "email_verification_otp_minutes",
        "password_reset_otp_minutes",
        "otp_length",
        "otp_max_attempts",
        "google_redirect_uri",
    ):
        print_setting_status(
            name
        )

    print_setting_status(
        "smtp_password",
        secret=True,
    )

    print_setting_status(
        "google_client_id",
        secret=True,
    )

    print_setting_status(
        "google_client_secret",
        secret=True,
    )

    print()
    print(
        "[3/5] Email enabled check"
    )
    print()

    email_enabled = get_setting(
        "email_enabled"
    )

    if email_enabled is True:
        print(
            "PASS EMAIL_ENABLED is active"
        )
    else:
        print(
            "FAIL EMAIL_ENABLED is not active in loaded settings"
        )

    print()
    print(
        "[4/5] Registered auth routes"
    )
    print()

    routes = list_auth_routes()

    if not routes:
        print(
            "FAIL no /auth/ FastAPI routes found"
        )
    else:
        for route in routes:
            methods = ",".join(
                route["methods"]
            )

            print(
                f"{methods:12} "
                f"{route['path']}"
            )

    print()
    print(
        "[5/5] Expected flow coverage"
    )
    print()

    route_paths = {
        row["path"]
        for row in routes
    }

    checks = {
        "signup/register": any(
            token in path
            for path in route_paths
            for token in (
                "/register",
                "/signup",
            )
        ),
        "email verification": any(
            token in path
            for path in route_paths
            for token in (
                "verify",
                "verification",
            )
        ),
        "forgot password": any(
            token in path
            for path in route_paths
            for token in (
                "forgot",
                "password-reset",
                "reset-password",
            )
        ),
        "google oauth": any(
            "google" in path
            for path in route_paths
        ),
    }

    for name, passed in checks.items():
        status = (
            "PASS"
            if passed
            else "CHECK"
        )

        print(
            f"{status:5} {name}"
        )

    print()
    print(
        "================================================="
    )
    print(
        " DIAGNOSTIC COMPLETE"
    )
    print(
        "================================================="
    )
    print()

    print(
        "SMTP transport itself already passed separately."
    )

    print(
        "If OTP still does not arrive, "
        "inspect auth service -> email service calls."
    )

    print()


if __name__ == "__main__":
    main()