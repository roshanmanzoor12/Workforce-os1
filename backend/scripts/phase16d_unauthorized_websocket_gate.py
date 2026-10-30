from __future__ import annotations

import asyncio
import json
import os
import sys
import uuid
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import (
    quote,
)

import websockets


# =========================================================
# PYTHON PATH BOOTSTRAP
# =========================================================


BACKEND_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

BACKEND_ROOT_TEXT = str(
    BACKEND_ROOT
)

if (
    BACKEND_ROOT_TEXT
    not in sys.path
):
    sys.path.insert(
        0,
        BACKEND_ROOT_TEXT,
    )


# =========================================================
# CONFIG
# =========================================================


API_BASE = os.getenv(
    "WF_API_BASE",
    "http://127.0.0.1:8001/api/v1",
).rstrip("/")

WS_BASE = os.getenv(
    "WF_WS_BASE",
    "ws://127.0.0.1:8001",
).rstrip("/")

WS_PATH = os.getenv(
    "WF_CHANNEL_WS_PATH",
    (
        "/api/v1/workspaces/"
        "{workspace_id}/channels/"
        "{channel_id}/realtime/ws"
    ),
)

WORKSPACE_ID = uuid.UUID(
    os.environ[
        "WF_WORKSPACE_ID"
    ]
)

CHANNEL_ID = uuid.UUID(
    os.environ[
        "WF_CHANNEL_ID"
    ]
)

TOKEN = (
    os.getenv(
        "WF_TOKEN_B"
    )
    or os.getenv(
        "WF_TOKEN_A"
    )
)

if not TOKEN:
    raise RuntimeError(
        "WF_TOKEN_B or WF_TOKEN_A "
        "must be configured."
    )


TIMEOUT_SECONDS = float(
    os.getenv(
        "WF_WS_TIMEOUT_SECONDS",
        "12",
    )
)


# =========================================================
# ERRORS
# =========================================================


class GateFailure(
    RuntimeError
):
    pass


# =========================================================
# HTTP
# =========================================================


def http_json(
    *,
    method: str,
    url: str,
    token: str | None = None,
    body: dict[
        str,
        Any,
    ]
    | None = None,
) -> tuple[
    int,
    Any,
]:
    data: bytes | None = None

    headers = {
        "Accept": "application/json",
    }

    if token:
        headers[
            "Authorization"
        ] = (
            f"Bearer {token}"
        )

    if body is not None:
        data = json.dumps(
            body
        ).encode(
            "utf-8"
        )

        headers[
            "Content-Type"
        ] = "application/json"

    request = (
        urllib.request.Request(
            url=url,
            method=method,
            data=data,
            headers=headers,
        )
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=TIMEOUT_SECONDS,
        ) as response:
            raw = response.read()

            if raw:
                payload = json.loads(
                    raw.decode(
                        "utf-8"
                    )
                )
            else:
                payload = None

            return (
                int(
                    response.status
                ),
                payload,
            )

    except urllib.error.HTTPError as exc:
        raw = exc.read()

        try:
            payload = json.loads(
                raw.decode(
                    "utf-8"
                )
            )

        except Exception:
            payload = raw.decode(
                "utf-8",
                errors="replace",
            )

        raise GateFailure(
            f"HTTP {exc.code} for "
            f"{method} {url}: "
            f"{payload}"
        ) from exc

    except Exception as exc:
        raise GateFailure(
            "HTTP request failed for "
            f"{method} {url}: {exc}"
        ) from exc


# =========================================================
# TICKET
# =========================================================


def create_ticket() -> str:
    url = (
        f"{API_BASE}/workspaces/"
        f"{WORKSPACE_ID}/channels/"
        f"{CHANNEL_ID}/realtime/ticket"
    )

    status_code, payload = (
        http_json(
            method="POST",
            url=url,
            token=TOKEN,
        )
    )

    if status_code != 200:
        raise GateFailure(
            "Realtime ticket endpoint "
            f"returned {status_code}."
        )

    if not isinstance(
        payload,
        dict,
    ):
        raise GateFailure(
            "Realtime ticket response "
            "was not an object."
        )

    ticket = (
        payload.get(
            "ticket"
        )
        or payload.get(
            "realtime_ticket"
        )
        or payload.get(
            "token"
        )
    )

    if not isinstance(
        ticket,
        str,
    ):
        raise GateFailure(
            "Realtime ticket was "
            "missing from response."
        )

    if len(
        ticket
    ) < 20:
        raise GateFailure(
            "Realtime ticket was "
            "unexpectedly short."
        )

    return ticket


# =========================================================
# URL HELPERS
# =========================================================


def base_websocket_url() -> str:
    path = (
        WS_PATH
        .replace(
            "{workspace_id}",
            str(
                WORKSPACE_ID
            ),
        )
        .replace(
            "{channel_id}",
            str(
                CHANNEL_ID
            ),
        )
    )

    return (
        f"{WS_BASE}{path}"
    )


def ticket_websocket_url(
    ticket: str,
) -> str:
    return (
        f"{base_websocket_url()}"
        f"?ticket={quote(ticket, safe='')}"
    )


# =========================================================
# WEBSOCKET RESULT HELPERS
# =========================================================


def exception_status(
    exc: BaseException,
) -> int | None:
    """
    websockets library versions expose handshake status
    through slightly different exception shapes.

    This extracts a status code when available without
    coupling the gate to one exact websockets version.
    """

    response = getattr(
        exc,
        "response",
        None,
    )

    if response is not None:
        status_code = getattr(
            response,
            "status_code",
            None,
        )

        if status_code is None:
            status_code = getattr(
                response,
                "status",
                None,
            )

        if status_code is not None:
            try:
                return int(
                    status_code
                )
            except (
                TypeError,
                ValueError,
            ):
                pass

    status_code = getattr(
        exc,
        "status_code",
        None,
    )

    if status_code is not None:
        try:
            return int(
                status_code
            )
        except (
            TypeError,
            ValueError,
        ):
            pass

    return None


def rejection_is_acceptable(
    exc: BaseException,
) -> bool:
    """
    A rejected WebSocket handshake is the expected result.

    FastAPI / Starlette commonly produce 403 for rejected
    WebSocket handshakes. Validation or gateway layers may
    expose another HTTP 4xx status instead.

    Any 4xx handshake rejection is accepted here.
    """

    status_code = (
        exception_status(
            exc
        )
    )

    if status_code is not None:
        return (
            400
            <= status_code
            < 500
        )

    name = (
        type(
            exc
        ).__name__.lower()
    )

    text = str(
        exc
    ).lower()

    rejection_markers = (
        "invalidstatus",
        "invalid status",
        "http 4",
        "403",
        "401",
        "400",
        "422",
        "handshake",
        "rejected",
        "forbidden",
        "unauthorized",
    )

    return any(
        marker in name
        or marker in text
        for marker
        in rejection_markers
    )


# =========================================================
# EXPECT REJECTION
# =========================================================


async def expect_rejected(
    *,
    url: str,
    label: str,
) -> None:
    try:
        async with websockets.connect(
            url,
            open_timeout=TIMEOUT_SECONDS,
            close_timeout=3,
        ) as websocket:
            # Even if the server accepts and immediately closes,
            # an unauthorized connection must not survive as a
            # usable authenticated channel.
            try:
                await asyncio.wait_for(
                    websocket.recv(),
                    timeout=1.0,
                )

            except Exception:
                pass

            raise GateFailure(
                f"{label} unexpectedly "
                "established a WebSocket connection."
            )

    except GateFailure:
        raise

    except Exception as exc:
        if not rejection_is_acceptable(
            exc
        ):
            raise GateFailure(
                f"{label} failed with an "
                "unexpected connection error: "
                f"{type(exc).__name__}: {exc}"
            ) from exc

        status_code = (
            exception_status(
                exc
            )
        )

        if status_code is not None:
            print(
                f"Rejected HTTP status: "
                f"{status_code}"
            )


# =========================================================
# VALID CONNECTION
# =========================================================


async def consume_valid_ticket(
    ticket: str,
) -> None:
    url = ticket_websocket_url(
        ticket
    )

    try:
        async with websockets.connect(
            url,
            open_timeout=TIMEOUT_SECONDS,
            close_timeout=3,
        ):
            # Successful handshake is enough to consume
            # and certify the valid one-time ticket.
            await asyncio.sleep(
                0.2
            )

    except Exception as exc:
        raise GateFailure(
            "Fresh valid realtime ticket "
            "was rejected: "
            f"{type(exc).__name__}: {exc}"
        ) from exc


# =========================================================
# MAIN
# =========================================================


async def main_async() -> None:
    print(
        "================================================="
    )
    print(
        " WorkforceOS Phase 16D Unauthorized "
        "WebSocket Gate"
    )
    print(
        "================================================="
    )
    print()

    # =====================================================
    # 1/6 NO TICKET
    # =====================================================

    print(
        "[1/6] Connecting without realtime ticket..."
    )

    await expect_rejected(
        url=base_websocket_url(),
        label="No-ticket connection",
    )

    print(
        "PASS: Missing ticket rejected"
    )
    print()

    # =====================================================
    # 2/6 BOGUS TICKET
    # =====================================================

    print(
        "[2/6] Connecting with bogus ticket..."
    )

    bogus_ticket = (
        "phase16d-invalid-ticket-"
        + uuid.uuid4().hex
        + uuid.uuid4().hex
    )

    await expect_rejected(
        url=ticket_websocket_url(
            bogus_ticket
        ),
        label="Bogus-ticket connection",
    )

    print(
        "PASS: Bogus ticket rejected"
    )
    print()

    # =====================================================
    # 3/6 ISSUE VALID TICKET
    # =====================================================

    print(
        "[3/6] Issuing valid realtime ticket..."
    )

    valid_ticket = (
        await asyncio.to_thread(
            create_ticket
        )
    )

    print(
        "PASS: Valid ticket issued"
    )
    print()

    # =====================================================
    # 4/6 VALID TICKET ACCEPTED
    # =====================================================

    print(
        "[4/6] Connecting with fresh valid ticket..."
    )

    await consume_valid_ticket(
        valid_ticket
    )

    print(
        "PASS: Fresh valid ticket accepted"
    )
    print()

    # =====================================================
    # 5/6 REUSE SAME TICKET
    # =====================================================

    print(
        "[5/6] Reusing consumed realtime ticket..."
    )

    await expect_rejected(
        url=ticket_websocket_url(
            valid_ticket
        ),
        label="Consumed-ticket reuse",
    )

    print(
        "PASS: Consumed ticket reuse rejected"
    )
    print()

    # =====================================================
    # 6/6 FRESH TICKET STILL WORKS
    # =====================================================

    print(
        "[6/6] Verifying fresh ticket still connects..."
    )

    second_ticket = (
        await asyncio.to_thread(
            create_ticket
        )
    )

    if (
        second_ticket
        == valid_ticket
    ):
        raise GateFailure(
            "Ticket issuer reused an already "
            "consumed ticket value."
        )

    await consume_valid_ticket(
        second_ticket
    )

    print(
        "PASS: Fresh independent ticket accepted"
    )

    print()
    print(
        "================================================="
    )
    print(
        " PHASE 16D UNAUTHORIZED WEBSOCKET PASS"
    )
    print(
        "================================================="
    )


# =========================================================
# ENTRYPOINT
# =========================================================


def main() -> None:
    try:
        asyncio.run(
            main_async()
        )

    except Exception as exc:
        print(
            f"FAIL: {exc}",
            file=sys.stderr,
        )

        raise


if __name__ == "__main__":
    main()