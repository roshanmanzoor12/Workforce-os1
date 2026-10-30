from __future__ import annotations

import inspect
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


AUTH_ROOT = (
    BACKEND_ROOT
    / "app"
    / "modules"
    / "auth"
)


SEARCH_TERMS = (
    "signup",
    "forgot_password",
    "forgot-password",
    "send_email",
    "send_mail",
    "smtp",
    "email_service",
    "verification",
    "password_reset",
    "issue_email_verification",
    "issue_password_reset",
    "resend_verification",
)


def separator(
    title: str,
) -> None:
    print()
    print(
        "=" * 76
    )
    print(
        f" {title}"
    )
    print(
        "=" * 76
    )
    print()


def read_text(
    path: Path,
) -> str:
    try:
        return path.read_text(
            encoding="utf-8"
        )
    except UnicodeDecodeError:
        return path.read_text(
            encoding="utf-8-sig"
        )


def find_auth_files() -> list[Path]:
    if not AUTH_ROOT.exists():
        raise RuntimeError(
            f"Auth directory not found: {AUTH_ROOT}"
        )

    return sorted(
        AUTH_ROOT.rglob(
            "*.py"
        )
    )


def print_matching_lines(
    path: Path,
) -> None:
    text = read_text(
        path
    )

    matches: list[
        tuple[int, str]
    ] = []

    for line_number, raw_line in enumerate(
        text.splitlines(),
        start=1,
    ):
        line = raw_line.rstrip()

        lowered = line.lower()

        if any(
            term.lower() in lowered
            for term in SEARCH_TERMS
        ):
            matches.append(
                (
                    line_number,
                    line.strip(),
                )
            )

    if not matches:
        return

    print(
        "FILE:",
        path.relative_to(
            BACKEND_ROOT
        ),
    )

    for line_number, line in matches:
        print(
            f"  {line_number:4}: {line}"
        )

    print()


def inspect_module_exports(
    module_name: str,
) -> None:
    separator(
        f"MODULE: {module_name}"
    )

    try:
        module = __import__(
            module_name,
            fromlist=["*"],
        )
    except Exception as exc:
        print(
            f"IMPORT FAIL: "
            f"{type(exc).__name__}: {exc}"
        )

        return

    names = sorted(
        name
        for name in dir(
            module
        )
        if not name.startswith(
            "_"
        )
    )

    for name in names:
        value = getattr(
            module,
            name,
        )

        if not callable(
            value
        ):
            continue

        lowered = name.lower()

        if not any(
            token in lowered
            for token in (
                "signup",
                "forgot",
                "email",
                "verification",
                "reset",
                "send",
            )
        ):
            continue

        try:
            signature = inspect.signature(
                value
            )

            print(
                f"{name}{signature}"
            )
        except Exception:
            print(
                name
            )


def find_email_modules() -> list[Path]:
    matches: list[Path] = []

    app_root = (
        BACKEND_ROOT
        / "app"
    )

    for path in app_root.rglob(
        "*.py"
    ):
        text = read_text(
            path
        ).lower()

        if any(
            token in text
            for token in (
                "smtplib",
                "smtp_host",
                "smtp_username",
                "smtp_password",
                "emailmessage",
                "send_message",
                "sendmail",
            )
        ):
            matches.append(
                path
            )

    return sorted(
        set(
            matches
        )
    )


def inspect_email_module(
    path: Path,
) -> None:
    text = read_text(
        path
    )

    print(
        "FILE:",
        path.relative_to(
            BACKEND_ROOT
        ),
    )

    interesting = (
        "class ",
        "def ",
        "async def ",
        "smtp",
        "send",
        "email_enabled",
        "from_email",
    )

    for line_number, raw_line in enumerate(
        text.splitlines(),
        start=1,
    ):
        stripped = raw_line.strip()

        lowered = stripped.lower()

        if any(
            token in lowered
            for token in interesting
        ):
            print(
                f"  {line_number:4}: {stripped}"
            )

    print()


def main() -> None:
    separator(
        "WorkforceOS Auth Email Dispatch Trace"
    )

    print(
        "Auth directory:",
        AUTH_ROOT,
    )

    separator(
        "AUTH SOURCE REFERENCES"
    )

    files = find_auth_files()

    for path in files:
        print_matching_lines(
            path
        )

    separator(
        "AUTH MODULE CALLABLES"
    )

    for module_name in (
        "app.modules.auth.service",
        "app.modules.auth.email_verification",
        "app.modules.auth.password_reset",
        "app.modules.auth.router",
    ):
        inspect_module_exports(
            module_name
        )

    separator(
        "EMAIL / SMTP IMPLEMENTATION FILES"
    )

    email_modules = (
        find_email_modules()
    )

    if not email_modules:
        print(
            "FAIL no application SMTP/email implementation "
            "file detected under app/."
        )
    else:
        for path in email_modules:
            inspect_email_module(
                path
            )

    separator(
        "INTERPRETATION"
    )

    print(
        "Check whether signup() calls an email sender "
        "after issuing the verification OTP."
    )

    print(
        "Check whether forgot_password() calls an email sender "
        "after issuing the password-reset OTP."
    )

    print(
        "If OTP issuing exists but no send call exists, "
        "that is the integration bug."
    )

    print(
        "If send calls exist, the next step is live endpoint tracing."
    )

    print()


if __name__ == "__main__":
    main()