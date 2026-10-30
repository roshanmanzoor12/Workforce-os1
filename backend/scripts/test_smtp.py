from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from pathlib import Path


ENV_FILE = Path(r"C:\workforce-os\.env")


def load_env() -> None:
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

        key, value = line.split("=", 1)

        key = key.strip()
        value = value.strip()

        if (
            len(value) >= 2
            and value[0] == value[-1]
            and value[0] in {"'", '"'}
        ):
            value = value[1:-1]

        os.environ.setdefault(
            key,
            value,
        )


def require(name: str) -> str:
    value = os.environ.get(name)

    if not value:
        raise RuntimeError(
            f"Missing environment variable: {name}"
        )

    return value


def main() -> None:
    load_env()

    host = require("SMTP_HOST")
    port = int(require("SMTP_PORT"))
    username = require("SMTP_USERNAME")
    password = require("SMTP_PASSWORD")
    from_email = require("SMTP_FROM_EMAIL")

    message = EmailMessage()

    message["Subject"] = "WorkforceOS SMTP Test"
    message["From"] = from_email
    message["To"] = username

    message.set_content(
        "WorkforceOS SMTP configuration is working."
    )

    print(f"SMTP host: {host}")
    print(f"SMTP port: {port}")
    print(f"SMTP user: {username}")
    print("SMTP password: <hidden>")

    with smtplib.SMTP(
        host,
        port,
        timeout=30,
    ) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()

        print("PASS TLS connection")

        smtp.login(
            username,
            password,
        )

        print("PASS SMTP authentication")

        smtp.send_message(
            message
        )

        print("PASS test email sent")


if __name__ == "__main__":
    main()