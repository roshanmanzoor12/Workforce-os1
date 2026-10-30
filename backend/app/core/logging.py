import logging
import sys
from contextvars import ContextVar
from typing import Optional

import structlog

from app.config import settings


# =========================================================
# REQUEST CONTEXT
# =========================================================

request_id_context: ContextVar[Optional[str]] = ContextVar(
    "request_id",
    default=None,
)

user_id_context: ContextVar[Optional[str]] = ContextVar(
    "user_id",
    default=None,
)

workspace_id_context: ContextVar[Optional[str]] = ContextVar(
    "workspace_id",
    default=None,
)


# =========================================================
# CONTEXT HELPERS
# =========================================================

def set_request_context(
    *,
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
    workspace_id: Optional[str] = None,
) -> None:
    if request_id is not None:
        request_id_context.set(request_id)

    if user_id is not None:
        user_id_context.set(user_id)

    if workspace_id is not None:
        workspace_id_context.set(workspace_id)


def clear_request_context() -> None:
    request_id_context.set(None)
    user_id_context.set(None)
    workspace_id_context.set(None)


def add_request_context(
    logger,
    method_name,
    event_dict,
):
    request_id = request_id_context.get()
    user_id = user_id_context.get()
    workspace_id = workspace_id_context.get()

    if request_id:
        event_dict["request_id"] = request_id

    if user_id:
        event_dict["user_id"] = user_id

    if workspace_id:
        event_dict["workspace_id"] = workspace_id

    return event_dict


# =========================================================
# SENSITIVE DATA FILTER
# =========================================================

SENSITIVE_FIELDS = {
    "password",
    "password_hash",
    "token",
    "access_token",
    "refresh_token",
    "authorization",
    "jwt",
    "jwt_secret",
    "otp",
    "otp_hash",
    "secret",
    "api_key",
    "stripe_secret_key",
    "smtp_password",
    "s3_secret_key",
    "livekit_api_secret",
    "turn_password",
}


def redact_sensitive_data(
    logger,
    method_name,
    event_dict,
):
    for key in list(event_dict.keys()):
        if key.lower() in SENSITIVE_FIELDS:
            event_dict[key] = "[REDACTED]"

    return event_dict


# =========================================================
# LOGGING CONFIGURATION
# =========================================================

def configure_logging() -> None:
    log_level = getattr(
        logging,
        settings.log_level.upper(),
        logging.INFO,
    )

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        add_request_context,
        redact_sensitive_data,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(
            fmt="iso",
            utc=True,
        ),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if settings.log_format.lower() == "json":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(
            colors=sys.stdout.isatty()
        )

    structlog.configure(
        processors=[
            *shared_processors,
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            log_level
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(
            file=sys.stdout
        ),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        stream=sys.stdout,
        force=True,
    )

    # Reduce noisy libraries
    logging.getLogger("uvicorn.access").setLevel(
        logging.WARNING
    )

    logging.getLogger("botocore").setLevel(
        logging.WARNING
    )

    logging.getLogger("boto3").setLevel(
        logging.WARNING
    )

    logging.getLogger("urllib3").setLevel(
        logging.WARNING
    )


# =========================================================
# LOGGER FACTORY
# =========================================================

def get_logger(name: str):
    return structlog.get_logger(name)