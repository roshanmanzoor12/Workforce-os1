from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.core.exceptions import (
    WorkforceError,
    error_payload,
)
from app.core.logging import get_logger
from app.middleware.request_id import get_request_id


logger = get_logger(__name__)


# =========================================================
# WORKFORCEOS APPLICATION ERRORS
# =========================================================

async def workforce_error_handler(
    request: Request,
    exc: WorkforceError,
) -> JSONResponse:
    """
    Convert expected WorkforceOS application exceptions
    into a consistent API response.

    Example:

        raise ResourceNotFound("Employee not found")

    becomes:

        {
            "error": {
                "code": "RESOURCE_NOT_FOUND",
                "message": "Employee not found",
                "request_id": "..."
            }
        }
    """

    request_id = get_request_id(request)

    logger.warning(
        "workforce_error",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        error_code=exc.code,
        status_code=exc.status_code,
        message=exc.message,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload(
            exc,
            request_id=request_id,
        ),
        headers=_request_id_headers(
            request_id
        ),
    )


# =========================================================
# FASTAPI / PYDANTIC VALIDATION ERRORS
# =========================================================

async def validation_error_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """
    Normalize FastAPI/Pydantic request validation errors.

    Used for:
    - invalid body fields
    - missing required fields
    - query validation
    - path validation
    """

    request_id = get_request_id(request)

    errors: list[dict[str, Any]] = []

    for error in exc.errors():
        location = [
            str(item)
            for item in error.get(
                "loc",
                [],
            )
        ]

        errors.append(
            {
                "field": ".".join(location),
                "message": error.get(
                    "msg",
                    "Invalid value.",
                ),
                "type": error.get(
                    "type",
                    "validation_error",
                ),
            }
        )

    logger.info(
        "request_validation_failed",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        errors=errors,
    )

    content: dict[str, Any] = {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Request validation failed.",
            "details": {
                "fields": errors,
            },
        }
    }

    if request_id:
        content["error"][
            "request_id"
        ] = request_id

    return JSONResponse(
        status_code=422,
        content=content,
        headers=_request_id_headers(
            request_id
        ),
    )


# =========================================================
# HTTP ERRORS
# =========================================================

async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    """
    Normalize framework-level HTTP exceptions.

    Examples:
    - 404 route not found
    - explicit HTTPException
    - method not allowed
    """

    request_id = get_request_id(request)

    detail = exc.detail

    if isinstance(detail, str):
        message = detail

    else:
        message = "HTTP request failed."

    code = _http_error_code(
        exc.status_code
    )

    content: dict[str, Any] = {
        "error": {
            "code": code,
            "message": message,
        }
    }

    if (
        not isinstance(
            detail,
            str,
        )
        and detail is not None
    ):
        content["error"]["details"] = detail

    if request_id:
        content["error"][
            "request_id"
        ] = request_id

    return JSONResponse(
        status_code=exc.status_code,
        content=content,
        headers={
            **(
                exc.headers
                or {}
            ),
            **_request_id_headers(
                request_id
            ),
        },
    )


# =========================================================
# UNHANDLED SERVER ERRORS
# =========================================================

async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Catch unexpected server exceptions.

    Important:
    Internal traceback/error details must not be returned
    to production users.
    """

    request_id = get_request_id(request)

    logger.exception(
        "unhandled_exception",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        exception_type=type(
            exc
        ).__name__,
        error=str(exc),
    )

    content: dict[str, Any] = {
        "error": {
            "code": "INTERNAL_SERVER_ERROR",
            "message": (
                "An unexpected server error occurred."
            ),
        }
    }

    if request_id:
        content["error"][
            "request_id"
        ] = request_id

    # Development convenience only.
    # Never expose exception details in production.
    if (
        settings.debug
        and not settings.is_production
    ):
        content["error"][
            "debug"
        ] = {
            "type": type(
                exc
            ).__name__,
            "message": str(
                exc
            ),
        }

    return JSONResponse(
        status_code=500,
        content=content,
        headers=_request_id_headers(
            request_id
        ),
    )


# =========================================================
# HANDLER REGISTRATION
# =========================================================

def register_exception_handlers(
    app,
) -> None:
    """
    Register all global application exception handlers.

    Call once from main.py.
    """

    app.add_exception_handler(
        WorkforceError,
        workforce_error_handler,
    )

    app.add_exception_handler(
        RequestValidationError,
        validation_error_handler,
    )

    app.add_exception_handler(
        StarletteHTTPException,
        http_exception_handler,
    )

    app.add_exception_handler(
        Exception,
        unhandled_exception_handler,
    )


# =========================================================
# HELPERS
# =========================================================

def _request_id_headers(
    request_id: str | None,
) -> dict[str, str]:
    if not request_id:
        return {}

    return {
        "X-Request-ID": request_id,
    }


def _http_error_code(
    status_code: int,
) -> str:
    mapping = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        402: "PAYMENT_REQUIRED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        406: "NOT_ACCEPTABLE",
        408: "REQUEST_TIMEOUT",
        409: "CONFLICT",
        410: "GONE",
        413: "PAYLOAD_TOO_LARGE",
        415: "UNSUPPORTED_MEDIA_TYPE",
        422: "UNPROCESSABLE_ENTITY",
        429: "RATE_LIMIT_EXCEEDED",
        500: "INTERNAL_SERVER_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE",
        504: "GATEWAY_TIMEOUT",
    }

    return mapping.get(
        status_code,
        f"HTTP_{status_code}",
    )