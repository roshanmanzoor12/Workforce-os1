from __future__ import annotations

import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logging import (
    clear_request_context,
    set_request_context,
)


REQUEST_ID_HEADER = "X-Request-ID"


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Adds a unique request ID to every HTTP request.

    Behavior:
    - accepts an existing X-Request-ID header when provided
    - otherwise generates a UUID
    - stores request_id on request.state
    - binds request_id into structured logging context
    - returns X-Request-ID in the response header

    This gives us traceability across:
    - API logs
    - errors
    - audit logs
    - background jobs
    - support/debugging
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        header_name: str = REQUEST_ID_HEADER,
    ) -> None:
        super().__init__(app)

        self.header_name = header_name


    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        request_id = (
            request.headers.get(self.header_name)
            or str(uuid.uuid4())
        )

        request.state.request_id = request_id

        set_request_context(
            request_id=request_id,
        )

        try:
            response = await call_next(request)

            response.headers[
                self.header_name
            ] = request_id

            return response

        finally:
            clear_request_context()


def get_request_id(
    request: Request,
) -> str | None:
    """
    Safe helper for retrieving the current request ID.

    Example:

        request_id = get_request_id(request)
    """

    return getattr(
        request.state,
        "request_id",
        None,
    )