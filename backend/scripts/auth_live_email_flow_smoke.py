from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


DEFAULT_API_BASE_URL = (
    "http://127.0.0.1:8001/api/v1"
)


@dataclass(frozen=True)
class HttpResult:
    status: int
    body: dict[str, Any] | list[Any] | str | None


def request_json(
    *,
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
) -> HttpResult:
    data: bytes | None = None

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    if payload is not None:
        data = json.dumps(
            payload
        ).encode(
            "utf-8"
        )

    request = urllib.request.Request(
        url=url,
        data=data,
        headers=headers,
        method=method,
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=30,
        ) as response:
            raw = response.read().decode(
                "utf-8"
            )

            return HttpResult(
                status=response.status,
                body=parse_body(
                    raw
                ),
            )

    except urllib.error.HTTPError as exc:
        raw = exc.read().decode(
            "utf-8",
            errors="replace",
        )

        return HttpResult(
            status=exc.code,
            body=parse_body(
                raw
            ),
        )

    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Unable to reach WorkforceOS backend: {exc}"
        ) from exc


def parse_body(
    raw: str,
) -> dict[str, Any] | list[Any] | str | None:
    if not raw:
        return None

    try:
        return json.loads(
            raw
        )
    except json.JSONDecodeError:
        return raw


def print_result(
    title: str,
    result: HttpResult,
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

    print(
        "HTTP status:",
        result.status,
    )

    print(
        "Response:"
    )

    print(
        json.dumps(
            result.body,
            indent=2,
            default=str,
        )
        if isinstance(
            result.body,
            (
                dict,
                list,
            ),
        )
        else result.body
    )

    print()


def run_signup(
    *,
    api_base_url: str,
    email: str,
    username: str,
    password: str,
) -> HttpResult:
    return request_json(
        method="POST",
        url=(
            f"{api_base_url}"
            "/auth/signup"
        ),
        payload={
            "email": email,
            "username": username,
            "password": password,
            "confirm_password": password,
            "first_name": "SMTP",
            "last_name": "Test",
        },
    )


def run_forgot_password(
    *,
    api_base_url: str,
    email: str,
) -> HttpResult:
    return request_json(
        method="POST",
        url=(
            f"{api_base_url}"
            "/auth/forgot-password"
        ),
        payload={
            "email": email,
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "WorkforceOS live auth email-flow smoke test."
        )
    )

    parser.add_argument(
        "--email",
        required=True,
        help=(
            "Mailbox that should receive WorkforceOS OTP email."
        ),
    )

    parser.add_argument(
        "--username",
        default=None,
        help=(
            "Unique signup username. "
            "Required when --signup is used."
        ),
    )

    parser.add_argument(
        "--password",
        default=None,
        help=(
            "Development-only signup password. "
            "Required when --signup is used."
        ),
    )

    parser.add_argument(
        "--signup",
        action="store_true",
        help=(
            "Call POST /auth/signup."
        ),
    )

    parser.add_argument(
        "--forgot-password",
        action="store_true",
        help=(
            "Call POST /auth/forgot-password."
        ),
    )

    parser.add_argument(
        "--api-base-url",
        default=DEFAULT_API_BASE_URL,
    )

    args = parser.parse_args()

    if (
        not args.signup
        and not args.forgot_password
    ):
        parser.error(
            "Select --signup and/or --forgot-password."
        )

    if args.signup:
        if not args.username:
            parser.error(
                "--username is required with --signup."
            )

        if not args.password:
            parser.error(
                "--password is required with --signup."
            )

    api_base_url = (
        args.api_base_url.rstrip(
            "/"
        )
    )

    print()
    print(
        "============================================================"
    )
    print(
        " WorkforceOS Live Auth Email Flow Smoke"
    )
    print(
        "============================================================"
    )
    print()

    print(
        "API:",
        api_base_url,
    )

    print(
        "Email:",
        args.email,
    )

    if args.signup:
        result = run_signup(
            api_base_url=api_base_url,
            email=args.email,
            username=args.username,
            password=args.password,
        )

        print_result(
            "SIGNUP",
            result,
        )

        if result.status >= 500:
            raise RuntimeError(
                "Signup returned a server error."
            )

        if result.status >= 400:
            print(
                "CHECK signup request was rejected before "
                "successful completion."
            )
        else:
            print(
                "PASS signup endpoint completed."
            )

            print(
                "Check the mailbox for the verification OTP."
            )

    if args.forgot_password:
        result = run_forgot_password(
            api_base_url=api_base_url,
            email=args.email,
        )

        print_result(
            "FORGOT PASSWORD",
            result,
        )

        if result.status >= 500:
            raise RuntimeError(
                "Forgot-password returned a server error."
            )

        if result.status >= 400:
            print(
                "CHECK forgot-password request was rejected."
            )
        else:
            print(
                "PASS forgot-password endpoint completed."
            )

            print(
                "Check the mailbox for the password-reset OTP."
            )

    print()
    print(
        "============================================================"
    )
    print(
        " LIVE AUTH EMAIL TEST COMPLETE"
    )
    print(
        "============================================================"
    )
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(
            "\nCancelled."
        )

        sys.exit(
            130
        )