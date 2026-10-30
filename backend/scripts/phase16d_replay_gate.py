from __future__ import annotations

import asyncio
import inspect
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
    os.environ["WF_WORKSPACE_ID"]
)

CHANNEL_ID = uuid.UUID(
    os.environ["WF_CHANNEL_ID"]
)

TOKEN_A = os.environ[
    "WF_TOKEN_A"
]

TOKEN_B = os.environ[
    "WF_TOKEN_B"
]

TIMEOUT_SECONDS = float(
    os.getenv(
        "WF_REPLAY_TIMEOUT_SECONDS",
        "15",
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
        with (
            urllib.request.urlopen(
                request,
                timeout=TIMEOUT_SECONDS,
            )
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
            "Realtime ticket string "
            "was not found."
        )

    if len(
        ticket
    ) < 20:
        raise GateFailure(
            "Realtime ticket was "
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
# CHANNEL MESSAGE
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
                    "Phase 16D replay gate "
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
            "Message creation returned "
            f"{status_code}."
        )

    if not isinstance(
        payload,
        dict,
    ):
        raise GateFailure(
            "Message response was not "
            "an object."
        )

    raw_id = (
        payload.get(
            "id"
        )
        or payload.get(
            "message_id"
        )
    )

    if not raw_id:
        raise GateFailure(
            "Created message ID "
            "was missing."
        )

    return uuid.UUID(
        str(
            raw_id
        )
    )


# =========================================================
# EVENT HELPERS
# =========================================================


def normalize_event(
    value: Any,
) -> dict[
    str,
    Any,
]:
    if isinstance(
        value,
        dict,
    ):
        return value

    if isinstance(
        value,
        str,
    ):
        parsed = json.loads(
            value
        )

        if isinstance(
            parsed,
            dict,
        ):
            return parsed

    raise GateFailure(
        "Realtime event was not "
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
    candidates = [
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
            ]
        )

    for value in candidates:
        if value is None:
            continue

        try:
            return int(
                value
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


async def receive_message_event(
    websocket: Any,
    *,
    expected_message_id: uuid.UUID,
) -> dict[
    str,
    Any,
]:
    loop = (
        asyncio.get_running_loop()
    )

    deadline = (
        loop.time()
        + TIMEOUT_SECONDS
    )

    while True:
        remaining = (
            deadline
            - loop.time()
        )

        if remaining <= 0:
            raise GateFailure(
                "Timed out waiting for "
                "channel.message.created."
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

        if (
            event_message_id(
                event
            )
            != str(
                expected_message_id
            )
        ):
            continue

        return event


# =========================================================
# REPLAY BUS DISCOVERY
# =========================================================


def get_replay_bus() -> Any:
    """
    Resolve the real WorkforceOS channel realtime bus.

    The gate does not create a synthetic replay store.
    It searches the actual runtime module for an exported
    object implementing replay(...).
    """

    from app.modules.channels import (
        realtime_bus as realtime_bus_module,
    )

    preferred_names = (
        "channel_realtime_bus",
        "workspace_channel_realtime_bus",
        "realtime_bus",
    )

    for name in preferred_names:
        candidate = getattr(
            realtime_bus_module,
            name,
            None,
        )

        replay_method = getattr(
            candidate,
            "replay",
            None,
        )

        if callable(
            replay_method
        ):
            return candidate

    for name in dir(
        realtime_bus_module
    ):
        candidate = getattr(
            realtime_bus_module,
            name,
            None,
        )

        replay_method = getattr(
            candidate,
            "replay",
            None,
        )

        if callable(
            replay_method
        ):
            return candidate

    raise GateFailure(
        "Could not locate channel "
        "realtime bus replay() contract."
    )


async def replay_events(
    *,
    after_sequence: int,
    limit: int = 100,
) -> list[
    Any
]:
    bus = get_replay_bus()

    replay_method = getattr(
        bus,
        "replay",
    )

    result = replay_method(
        workspace_id=WORKSPACE_ID,
        channel_id=CHANNEL_ID,
        after_sequence=(
            after_sequence
        ),
        limit=limit,
    )

    if inspect.isawaitable(
        result
    ):
        result = await result

    return list(
        result
    )


def event_to_mapping(
    value: Any,
) -> dict[
    str,
    Any,
]:
    if isinstance(
        value,
        dict,
    ):
        return value

    for method_name in (
        "model_dump",
        "dict",
    ):
        method = getattr(
            value,
            method_name,
            None,
        )

        if callable(
            method
        ):
            mapped = method()

            if isinstance(
                mapped,
                dict,
            ):
                return mapped

    result: dict[
        str,
        Any,
    ] = {}

    for field in (
        "sequence",
        "sequence_id",
        "seq",
        "type",
        "event_type",
        "event",
        "payload",
        "workspace_id",
        "channel_id",
    ):
        if hasattr(
            value,
            field,
        ):
            result[
                field
            ] = getattr(
                value,
                field,
            )

    return result


# =========================================================
# MAIN
# =========================================================


async def main_async() -> None:
    print(
        "================================================="
    )
    print(
        " WorkforceOS Phase 16D Reconnect / Replay Gate"
    )
    print(
        "================================================="
    )
    print()

    # =====================================================
    # 1/8 INITIAL TICKET
    # =====================================================

    print(
        "[1/8] Issuing initial receiver ticket..."
    )

    ticket_b1 = (
        await asyncio.to_thread(
            create_ticket,
            token=TOKEN_B,
        )
    )

    print(
        "PASS: Initial receiver ticket issued"
    )
    print()

    # =====================================================
    # 2/8 INITIAL CONNECTION
    # =====================================================

    print(
        "[2/8] Connecting initial receiver WebSocket..."
    )

    async with websockets.connect(
        websocket_url(
            ticket_b1
        ),
        open_timeout=TIMEOUT_SECONDS,
        close_timeout=5,
    ) as websocket_b1:
        print(
            "PASS: Initial receiver connected"
        )
        print()

        # =================================================
        # 3/8 BASELINE LIVE EVENT
        # =================================================

        print(
            "[3/8] Creating baseline live event..."
        )

        baseline_message_id = (
            await asyncio.to_thread(
                create_message,
                token=TOKEN_A,
                marker=(
                    uuid.uuid4()
                    .hex[
                        :12
                    ]
                ),
            )
        )

        baseline_event = (
            await receive_message_event(
                websocket_b1,
                expected_message_id=(
                    baseline_message_id
                ),
            )
        )

        baseline_sequence = (
            event_sequence(
                baseline_event
            )
        )

        if baseline_sequence is None:
            raise GateFailure(
                "Baseline realtime event "
                "did not contain sequence."
            )

        print(
            "PASS: Baseline live event received"
        )
        print(
            "Baseline message ID:",
            baseline_message_id,
        )
        print(
            "Baseline sequence:",
            baseline_sequence,
        )
        print()

    # =====================================================
    # 4/8 OFFLINE EVENTS
    # =====================================================

    print(
        "[4/8] Receiver disconnected; "
        "creating missed events..."
    )

    missed_message_ids: list[
        uuid.UUID
    ] = []

    for _ in range(
        2
    ):
        message_id = (
            await asyncio.to_thread(
                create_message,
                token=TOKEN_A,
                marker=(
                    uuid.uuid4()
                    .hex[
                        :12
                    ]
                ),
            )
        )

        missed_message_ids.append(
            message_id
        )

    print(
        "PASS: Created 2 events while "
        "receiver was offline"
    )
    print()

    # =====================================================
    # 5/8 REPLAY STORE
    # =====================================================

    print(
        "[5/8] Replaying events after "
        "baseline sequence..."
    )

    replayed = await replay_events(
        after_sequence=(
            baseline_sequence
        ),
        limit=100,
    )

    replayed_maps = [
        event_to_mapping(
            item
        )
        for item
        in replayed
    ]

    expected_ids = {
        str(
            item
        )
        for item
        in missed_message_ids
    }

    matched: dict[
        str,
        dict[
            str,
            Any,
        ],
    ] = {}

    for event in replayed_maps:
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
            in expected_ids
        ):
            matched[
                message_id
            ] = event

    if len(
        matched
    ) != len(
        missed_message_ids
    ):
        found_ids = sorted(
            matched
        )

        raise GateFailure(
            "Replay did not contain all "
            "offline channel message events. "
            f"Expected={sorted(expected_ids)} "
            f"Found={found_ids}"
        )

    replay_sequences: list[
        int
    ] = []

    for message_id in (
        missed_message_ids
    ):
        event = matched[
            str(
                message_id
            )
        ]

        sequence = event_sequence(
            event
        )

        if sequence is None:
            raise GateFailure(
                "Replayed event missing "
                "sequence."
            )

        replay_sequences.append(
            sequence
        )

    if any(
        sequence
        <= baseline_sequence
        for sequence
        in replay_sequences
    ):
        raise GateFailure(
            "Replay returned sequence at "
            "or before baseline cursor."
        )

    if (
        replay_sequences
        != sorted(
            replay_sequences
        )
    ):
        raise GateFailure(
            "Replayed sequences are not "
            "strictly ordered."
        )

    if (
        len(
            set(
                replay_sequences
            )
        )
        != len(
            replay_sequences
        )
    ):
        raise GateFailure(
            "Replay returned duplicate "
            "sequence values."
        )

    print(
        "PASS: Offline events recovered "
        "from replay store"
    )

    print(
        "Replay sequences:",
        ", ".join(
            str(
                value
            )
            for value
            in replay_sequences
        ),
    )

    print()

    # =====================================================
    # 6/8 FRESH RECONNECT TICKET
    # =====================================================

    print(
        "[6/8] Issuing reconnect ticket..."
    )

    ticket_b2 = (
        await asyncio.to_thread(
            create_ticket,
            token=TOKEN_B,
        )
    )

    if (
        ticket_b2
        == ticket_b1
    ):
        raise GateFailure(
            "Reconnect ticket unexpectedly "
            "reused original ticket."
        )

    print(
        "PASS: Fresh reconnect ticket issued"
    )
    print()

    # =====================================================
    # 7/8 RECONNECT
    # =====================================================

    print(
        "[7/8] Reconnecting receiver WebSocket..."
    )

    async with websockets.connect(
        websocket_url(
            ticket_b2
        ),
        open_timeout=TIMEOUT_SECONDS,
        close_timeout=5,
    ) as websocket_b2:
        print(
            "PASS: Receiver reconnected"
        )
        print()

        # =================================================
        # 8/8 LIVE EVENT AFTER RECONNECT
        # =================================================

        print(
            "[8/8] Verifying live delivery "
            "after reconnect..."
        )

        final_message_id = (
            await asyncio.to_thread(
                create_message,
                token=TOKEN_A,
                marker=(
                    uuid.uuid4()
                    .hex[
                        :12
                    ]
                ),
            )
        )

        final_event = (
            await receive_message_event(
                websocket_b2,
                expected_message_id=(
                    final_message_id
                ),
            )
        )

        final_sequence = (
            event_sequence(
                final_event
            )
        )

        if final_sequence is None:
            raise GateFailure(
                "Reconnect live event "
                "missing sequence."
            )

        if final_sequence <= max(
            replay_sequences
        ):
            raise GateFailure(
                "Reconnect live sequence "
                "did not advance beyond "
                "replayed events."
            )

        print(
            "PASS: Live event received "
            "after reconnect"
        )

        print(
            "Final message ID:",
            final_message_id,
        )

        print(
            "Final sequence:",
            final_sequence,
        )

    print()
    print(
        "================================================="
    )
    print(
        " PHASE 16D RECONNECT / REPLAY PASS"
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