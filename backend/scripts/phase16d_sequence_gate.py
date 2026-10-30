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

TOKEN_A = os.environ[
    "WF_TOKEN_A"
]

TOKEN_B = os.environ[
    "WF_TOKEN_B"
]

TIMEOUT_SECONDS = float(
    os.getenv(
        "WF_WS_TIMEOUT_SECONDS",
        "12",
    )
)

EVENT_COUNT = int(
    os.getenv(
        "WF_SEQUENCE_EVENT_COUNT",
        "3",
    )
)

if EVENT_COUNT < 3:
    EVENT_COUNT = 3


# =========================================================
# ERROR
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
            f"HTTP request failed for "
            f"{method} {url}: {exc}"
        ) from exc


# =========================================================
# REALTIME TICKET
# =========================================================


def create_ticket(
    *,
    token: str,
) -> str:
    url = (
        f"{API_BASE}/workspaces/"
        f"{WORKSPACE_ID}/channels/"
        f"{CHANNEL_ID}/realtime/ticket"
    )

    status_code, payload = (
        http_json(
            method="POST",
            url=url,
            token=token,
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
            "Realtime ticket missing."
        )

    if len(
        ticket
    ) < 20:
        raise GateFailure(
            "Realtime ticket is "
            "unexpectedly short."
        )

    return ticket


def websocket_url(
    ticket: str,
) -> str:
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
        f"?ticket={ticket}"
    )


# =========================================================
# MESSAGE CREATION
# =========================================================


def create_message(
    *,
    token: str,
    marker: str,
) -> uuid.UUID:
    url = (
        f"{API_BASE}/workspace-channels/"
        f"{CHANNEL_ID}/messages"
    )

    status_code, payload = (
        http_json(
            method="POST",
            url=url,
            token=token,
            body={
                "content": (
                    "Phase 16D sequence gate "
                    f"{marker}"
                ),
            },
        )
    )

    if status_code not in {
        200,
        201,
    }:
        raise GateFailure(
            "Channel message creation "
            f"returned {status_code}."
        )

    if not isinstance(
        payload,
        dict,
    ):
        raise GateFailure(
            "Message response was not "
            "an object."
        )

    message_id = (
        payload.get(
            "id"
        )
        or payload.get(
            "message_id"
        )
    )

    if not message_id:
        raise GateFailure(
            "Created message ID "
            "was missing."
        )

    return uuid.UUID(
        str(
            message_id
        )
    )


# =========================================================
# EVENT NORMALIZATION
# =========================================================


def normalize_event(
    raw: Any,
) -> dict[
    str,
    Any,
]:
    if isinstance(
        raw,
        dict,
    ):
        return raw

    if isinstance(
        raw,
        bytes,
    ):
        raw = raw.decode(
            "utf-8"
        )

    if isinstance(
        raw,
        str,
    ):
        value = json.loads(
            raw
        )

        if isinstance(
            value,
            dict,
        ):
            return value

    raise GateFailure(
        "Realtime payload was not "
        "a JSON object."
    )


def event_type(
    event: dict[
        str,
        Any,
    ],
) -> str:
    value = (
        event.get(
            "type"
        )
        or event.get(
            "event_type"
        )
        or event.get(
            "event"
        )
    )

    return str(
        value or ""
    )


def event_sequence(
    event: dict[
        str,
        Any,
    ],
) -> int | None:
    candidates: list[
        Any
    ] = [
        event.get(
            "sequence"
        ),
        event.get(
            "sequence_id"
        ),
        event.get(
            "seq"
        ),
    ]

    payload = event.get(
        "payload"
    )

    if isinstance(
        payload,
        dict,
    ):
        candidates.extend(
            [
                payload.get(
                    "sequence"
                ),
                payload.get(
                    "sequence_id"
                ),
                payload.get(
                    "seq"
                ),
            ]
        )

    for candidate in candidates:
        if candidate is None:
            continue

        try:
            return int(
                candidate
            )

        except (
            TypeError,
            ValueError,
        ):
            continue

    return None


def event_message_id(
    event: dict[
        str,
        Any,
    ],
) -> str | None:
    payload = event.get(
        "payload"
    )

    if isinstance(
        payload,
        dict,
    ):
        value = (
            payload.get(
                "message_id"
            )
            or payload.get(
                "id"
            )
        )

        if value is not None:
            return str(
                value
            )

    value = event.get(
        "message_id"
    )

    if value is not None:
        return str(
            value
        )

    return None


# =========================================================
# RECEIVE
# =========================================================


async def receive_expected_messages(
    websocket: Any,
    *,
    expected_ids: list[
        uuid.UUID
    ],
) -> list[
    dict[
        str,
        Any,
    ]
]:
    expected = {
        str(
            message_id
        )
        for message_id
        in expected_ids
    }

    received: dict[
        str,
        dict[
            str,
            Any,
        ],
    ] = {}

    loop = (
        asyncio.get_running_loop()
    )

    deadline = (
        loop.time()
        + TIMEOUT_SECONDS
    )

    while (
        len(
            received
        )
        < len(
            expected
        )
    ):
        remaining = (
            deadline
            - loop.time()
        )

        if remaining <= 0:
            missing = (
                expected
                - set(
                    received
                )
            )

            raise GateFailure(
                "Timed out waiting for "
                "sequence events. Missing "
                f"message IDs: {sorted(missing)}"
            )

        raw = (
            await asyncio.wait_for(
                websocket.recv(),
                timeout=remaining,
            )
        )

        event = normalize_event(
            raw
        )

        if (
            event_type(
                event
            )
            != "channel.message.created"
        ):
            continue

        message_id = (
            event_message_id(
                event
            )
        )

        if (
            message_id
            not in expected
        ):
            continue

        if (
            message_id
            in received
        ):
            raise GateFailure(
                "Duplicate realtime message "
                f"event received: {message_id}"
            )

        received[
            message_id
        ] = event

    return [
        received[
            str(
                message_id
            )
        ]
        for message_id
        in expected_ids
    ]


# =========================================================
# SEQUENCE ASSERTIONS
# =========================================================


def assert_strict_sequence(
    events: list[
        dict[
            str,
            Any,
        ]
    ],
) -> list[
    int
]:
    sequences: list[
        int
    ] = []

    for index, event in enumerate(
        events,
        start=1,
    ):
        sequence = (
            event_sequence(
                event
            )
        )

        if sequence is None:
            raise GateFailure(
                "Realtime event "
                f"{index} is missing sequence."
            )

        sequences.append(
            sequence
        )

    if len(
        set(
            sequences
        )
    ) != len(
        sequences
    ):
        raise GateFailure(
            "Duplicate realtime sequence "
            f"detected: {sequences}"
        )

    for index in range(
        1,
        len(
            sequences
        ),
    ):
        previous = (
            sequences[
                index - 1
            ]
        )

        current = (
            sequences[
                index
            ]
        )

        if current <= previous:
            raise GateFailure(
                "Realtime sequence is not "
                "strictly increasing: "
                f"{sequences}"
            )

    return sequences


# =========================================================
# MAIN
# =========================================================


async def main_async() -> None:
    print(
        "================================================="
    )
    print(
        " WorkforceOS Phase 16D Strict Sequence Gate"
    )
    print(
        "================================================="
    )
    print()

    # =====================================================
    # 1/7 TICKET
    # =====================================================

    print(
        "[1/7] Issuing receiver realtime ticket..."
    )

    ticket = await asyncio.to_thread(
        create_ticket,
        token=TOKEN_B,
    )

    print(
        "PASS: Receiver ticket issued"
    )
    print()

    # =====================================================
    # 2/7 SOCKET
    # =====================================================

    print(
        "[2/7] Connecting receiver WebSocket..."
    )

    async with websockets.connect(
        websocket_url(
            ticket
        ),
        open_timeout=TIMEOUT_SECONDS,
        close_timeout=5,
    ) as websocket:
        print(
            "PASS: Receiver connected"
        )
        print()

        # =================================================
        # 3/7 CREATE EVENTS
        # =================================================

        print(
            f"[3/7] Creating {EVENT_COUNT} "
            "channel messages..."
        )

        message_ids: list[
            uuid.UUID
        ] = []

        for index in range(
            EVENT_COUNT
        ):
            message_id = (
                await asyncio.to_thread(
                    create_message,
                    token=TOKEN_A,
                    marker=(
                        f"{index + 1}-"
                        f"{uuid.uuid4().hex[:10]}"
                    ),
                )
            )

            message_ids.append(
                message_id
            )

            print(
                f"Message {index + 1}:",
                message_id,
            )

        print(
            "PASS: Channel messages created"
        )
        print()

        # =================================================
        # 4/7 RECEIVE EVENTS
        # =================================================

        print(
            "[4/7] Waiting for matching "
            "realtime events..."
        )

        events = (
            await receive_expected_messages(
                websocket,
                expected_ids=message_ids,
            )
        )

        print(
            "PASS: All matching realtime "
            "events received"
        )
        print()

        # =================================================
        # 5/7 EVENT IDENTITY
        # =================================================

        print(
            "[5/7] Verifying event identity "
            "and order..."
        )

        received_ids = [
            event_message_id(
                event
            )
            for event
            in events
        ]

        expected_ids = [
            str(
                message_id
            )
            for message_id
            in message_ids
        ]

        if (
            received_ids
            != expected_ids
        ):
            raise GateFailure(
                "Realtime event message order "
                "did not match creation order. "
                f"Expected={expected_ids} "
                f"Received={received_ids}"
            )

        print(
            "PASS: Event identities and "
            "message order match"
        )
        print()

        # =================================================
        # 6/7 STRICT SEQUENCE
        # =================================================

        print(
            "[6/7] Verifying strict realtime "
            "sequence progression..."
        )

        sequences = (
            assert_strict_sequence(
                events
            )
        )

        print(
            "PASS: Realtime sequences are "
            "unique and strictly increasing"
        )

        print(
            "Sequences:",
            ", ".join(
                str(
                    sequence
                )
                for sequence
                in sequences
            ),
        )

        print()

        # =================================================
        # 7/7 ADDITIONAL LIVE ADVANCE
        # =================================================

        print(
            "[7/7] Verifying sequence advances "
            "with another live event..."
        )

        extra_message_id = (
            await asyncio.to_thread(
                create_message,
                token=TOKEN_A,
                marker=(
                    "advance-"
                    f"{uuid.uuid4().hex[:10]}"
                ),
            )
        )

        extra_events = (
            await receive_expected_messages(
                websocket,
                expected_ids=[
                    extra_message_id
                ],
            )
        )

        extra_sequence = (
            event_sequence(
                extra_events[
                    0
                ]
            )
        )

        if extra_sequence is None:
            raise GateFailure(
                "Additional live event "
                "missing sequence."
            )

        if extra_sequence <= (
            sequences[
                -1
            ]
        ):
            raise GateFailure(
                "Additional live event did "
                "not advance sequence. "
                f"Previous={sequences[-1]} "
                f"Current={extra_sequence}"
            )

        if (
            event_message_id(
                extra_events[
                    0
                ]
            )
            != str(
                extra_message_id
            )
        ):
            raise GateFailure(
                "Additional realtime event "
                "message identity mismatch."
            )

        print(
            "PASS: Sequence advanced with "
            "additional live event"
        )

        print(
            "Additional message ID:",
            extra_message_id,
        )

        print(
            "Additional sequence:",
            extra_sequence,
        )

    print()
    print(
        "================================================="
    )
    print(
        " PHASE 16D STRICT SEQUENCE PASS"
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