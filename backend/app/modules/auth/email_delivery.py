from __future__ import annotations

import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr

from fastapi import HTTPException

from app.config import settings
from app.core.logging import get_logger


logger = get_logger(__name__)


def delivery_error(message: str) -> HTTPException:
    return HTTPException(
        status_code=503,
        detail=message,
    )


def send_auth_email_sync(
    recipient: str,
    subject: str,
    text: str,
) -> None:
    if not settings.email_enabled:
        raise delivery_error(
            "Email delivery is disabled. "
            "The verification or reset email was not sent."
        )

    host = (settings.smtp_host or "").strip()
    sender = (settings.smtp_from_email or "").strip()
    username = settings.smtp_username or ""
    password = settings.smtp_password or ""

    if not host or not sender:
        raise delivery_error(
            "Email delivery is not configured. "
            "SMTP host and sender email are required."
        )

    if bool(username) != bool(password):
        raise delivery_error(
            "SMTP credentials are incomplete. "
            "The email was not sent."
        )

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = formataddr(
        (
            settings.smtp_from_name or settings.app_name,
            sender,
        )
    )
    message["To"] = recipient
    message.set_content(text)

    context = ssl.create_default_context()
    port = int(settings.smtp_port)

    try:
        if port == 465:
            smtp_connection = smtplib.SMTP_SSL(
                host,
                port,
                timeout=20,
                context=context,
            )
        else:
            smtp_connection = smtplib.SMTP(
                host,
                port,
                timeout=20,
            )

        with smtp_connection as smtp:
            smtp.ehlo()

            if port != 465 and settings.smtp_use_tls:
                smtp.starttls(context=context)
                smtp.ehlo()

            if username:
                smtp.login(username, password)

            refused = smtp.send_message(
                message,
                from_addr=sender,
                to_addrs=[recipient],
            )

            if refused:
                raise delivery_error(
                    "The mail server refused the recipient. "
                    "The email was not sent."
                )

    except HTTPException:
        raise

    except smtplib.SMTPAuthenticationError as exc:
        logger.error(
            "auth_email_delivery_failed",
            failure_type="smtp_authentication",
            smtp_code=exc.smtp_code,
        )
        raise delivery_error(
            "The mail server rejected SMTP authentication. "
            "Check the configured credentials or app password."
        ) from None

    except smtplib.SMTPRecipientsRefused:
        logger.error(
            "auth_email_delivery_failed",
            failure_type="recipient_refused",
        )
        raise delivery_error(
            "The mail server refused the recipient. "
            "The email was not sent."
        ) from None

    except Exception as exc:
        logger.error(
            "auth_email_delivery_failed",
            failure_type=type(exc).__name__,
            smtp_code=getattr(exc, "smtp_code", None),
        )
        raise delivery_error(
            "The verification or reset email could not be sent. "
            "Check the backend email-delivery log and retry."
        ) from None

    logger.info(
        "auth_email_smtp_accepted",
    )


__all__ = [
    "send_auth_email_sync",
]