from __future__ import annotations

import asyncio
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any

import websockets


BACKEND_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(BACKEND_ROOT),
    )


class GateFailure(
    RuntimeError
):
    pass


def fail(
    message: str,
) -> None:
    raise GateFailure(
        message
    )


def env(
    name: str,
    *,
    required: bool = True,
    default: str = "",
) -> str:
    value = (
        os.getenv(
            name,
            default,
        )
        or ""
    ).strip()

    if required and not value:
        fail(
            f"Missing environment value: {name}"
        )

    return value


def heading(
    text: str,
) -> None:
    print()
    print(
        "=" * 49
    )
    print(
        f" {text}"
    )
    print(
        "=" * 49
    )
    print()


def http_json(
    *,
    method: str,
    url: str,
    token: str | None = None,
    body: dict[str, Any] | None = None,
    timeout: float = 15.0,
) -> tuple[
    int,
    Any,
]:
    headers = {
        "Accept": "application/json",
    }

    payload: bytes | None = None

    if token:
        headers[
            "Authorization"
        ] = f"Bearer {token}"

    if body is not None:
        headers[
            "Content-Type"
        ] = "application/json"

        payload = json.dumps(
            body
        ).encode(
            "utf-8"
        )

    request = urllib.request.Request(
        url=url,
        data=payload,
        headers=headers,
        method=method,
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=timeout,
        ) as response:
            raw = (
                response.read()
                .decode(
                    "utf-8"
                )
            )

            data: Any = None

            if raw.strip():
                try:
                    data = json.loads(
                        raw
                    )
                except json.JSONDecodeError:
                    data = raw

            return (
                int(
                    response.status
                ),
                data,
            )

    except urllib.error.HTTPError as exc:
        raw = (
            exc.read()
            .decode(
                "utf-8",
                errors="replace",
            )
        )

        try:
            detail: Any = json.loads(
                raw
            )
        except json.JSONDecodeError:
            detail = raw

        raise GateFailure(
            f"HTTP {exc.code} for "
            f"{method} {url}: "
            f"{detail}"
        ) from exc

    except urllib.error.URLError as exc:
        raise GateFailure(
            f"HTTP connection failed for "
            f"{method} {url}: "
            f"{exc}"
        ) from exc


def realtime_base_url(
    *,
    api_base: str,
    workspace_id: str,
    channel_id: str,
) -> str:
    return (
        f"{api_base.rstrip('/')}"
        f"/workspaces/"
        f"{workspace_id}"
        f"/channels/"
        f"{channel_id}"
        f"/realtime"
    )


def create_ticket(
    *,
    api_base: str,
    workspace_id: str,
    channel_id: str,
    token: str,
) -> str:
    url = (
        realtime_base_url(
            api_base=api_base,
            workspace_id=workspace_id,
            channel_id=channel_id,
        )
        + "/ticket"
    )

    status_code, data = http_json(
        method="POST",
        url=url,
        token=token,
    )

    if status_code != 200:
        fail(
            f"Realtime ticket endpoint "
            f"returned HTTP {status_code}."
        )

    if not isinstance(
        data,
        dict,
    ):
        fail(
            "Realtime ticket response "
            "was not a JSON object."
        )

    ticket = str(
        data.get(
            "ticket",
            "",
        )
        or ""
    ).strip()

    if not ticket:
        fail(
            "Realtime ticket response "
            "did not contain ticket."
        )

    if len(ticket) < 20:
        fail(
            "Realtime ticket is unexpectedly short."
        )

    return ticket


def websocket_url(
    *,
    ws_base: str,
    ws_path: str,
    workspace_id: str,
    channel_id: str,
    ticket: str,
) -> str:
    path = (
        ws_path
        .replace(
            "{workspace_id}",
            workspace_id,
        )
        .replace(
            "{channel_id}",
            channel_id,
        )
    )

    query = urllib.parse.urlencode(
        {
            "ticket": ticket,
        }
    )

    return (
        f"{ws_base.rstrip('/')}"
        f"{path}"
        f"?{query}"
    )


def send_message(
    *,
    api_base: str,
    channel_id: str,
    token: str,
    content: str,
) -> dict[str, Any]:
    url = (
        f"{api_base.rstrip('/')}"
        f"/workspace-channels/"
        f"{channel_id}"
        f"/messages"
    )

    status_code, data = http_json(
        method="POST",
        url=url,
        token=token,
        body={
            "content": content,
        },
    )

    if status_code != 201:
        fail(
            f"Message creation returned "
            f"HTTP {status_code}."
        )

    if not isinstance(
        data,
        dict,
    ):
        fail(
            "Message creation response "
            "was not a JSON object."
        )

    message_id = str(
        data.get(
            "id",
            "",
        )
        or ""
    ).strip()

    if not message_id:
        fail(
            "Created message response "
            "did not contain id."
        )

    return data


def decode_event(
    raw: Any,
) -> dict[str, Any] | None:
    if isinstance(
        raw,
        bytes,
    ):
        raw = raw.decode(
            "utf-8",
            errors="replace",
        )

    if not isinstance(
        raw,
        str,
    ):
        return None

    try:
        value = json.loads(
            raw
        )
    except json.JSONDecodeError:
        return None

    if not isinstance(
        value,
        dict,
    ):
        return None

    return value


def event_type(
    event: dict[str, Any],
) -> str:
    for key in (
        "type",
        "event_type",
        "name",
    ):
        value = event.get(
            key
        )

        if isinstance(
            value,
            str,
        ):
            return value

    return ""


def extract_message_id(
    event: dict[str, Any],
) -> str:
    direct = event.get(
        "message_id"
    )

    if direct is not None:
        return str(
            direct
        )

    payload = event.get(
        "payload"
    )

    if isinstance(
        payload,
        dict,
    ):
        value = payload.get(
            "message_id"
        )

        if value is not None:
            return str(
                value
            )

        nested_message = payload.get(
            "message"
        )

        if isinstance(
            nested_message,
            dict,
        ):
            nested_id = (
                nested_message.get(
                    "id"
                )
            )

            if nested_id is not None:
                return str(
                    nested_id
                )

    return ""


async def wait_for_message_event(
    websocket,
    *,
    message_id: str,
    timeout_seconds: float,
) -> dict[str, Any]:
    deadline = (
        asyncio.get_running_loop()
        .time()
        + timeout_seconds
    )

    observed: list[str] = []

    while True:
        remaining = (
            deadline
            - asyncio.get_running_loop()
            .time()
        )

        if remaining <= 0:
            fail(
                "Timed out waiting for "
                "message realtime event. "
                f"Observed event types={observed}"
            )

        raw = await asyncio.wait_for(
            websocket.recv(),
            timeout=remaining,
        )

        event = decode_event(
            raw
        )

        if event is None:
            continue

        kind = event_type(
            event
        )

        if kind:
            observed.append(
                kind
            )

        candidate_message_id = (
            extract_message_id(
                event
            )
        )

        if (
            candidate_message_id
            == message_id
        ):
            return event

        lowered = kind.lower()

        if (
            "message" in lowered
            and (
                not candidate_message_id
                or candidate_message_id
                == message_id
            )
        ):
            return event


async def main_async() -> None:
    heading(
        "WorkforceOS Phase 16D "
        "Two-Client Message Fanout"
    )

    api_base = env(
        "WF_API_BASE"
    )

    ws_base = env(
        "WF_WS_BASE"
    )

    ws_path = env(
        "WF_CHANNEL_WS_PATH"
    )

    token_a = env(
        "WF_TOKEN_A"
    )

    token_b = env(
        "WF_TOKEN_B"
    )

    workspace_id = env(
        "WF_WORKSPACE_ID"
    )

    channel_id = env(
        "WF_CHANNEL_ID"
    )

    timeout_seconds = float(
        env(
            "WF_WS_TIMEOUT_SECONDS",
            required=False,
            default="12",
        )
    )

    try:
        uuid.UUID(
            workspace_id
        )

        uuid.UUID(
            channel_id
        )

    except ValueError as exc:
        fail(
            "Workspace/channel environment IDs "
            "must be valid UUIDs."
        )

    print(
        "[1/6] Issuing client A realtime ticket..."
    )

    ticket_a = await asyncio.to_thread(
        create_ticket,
        api_base=api_base,
        workspace_id=workspace_id,
        channel_id=channel_id,
        token=token_a,
    )

    print(
        "PASS: Client A ticket issued"
    )

    print()
    print(
        "[2/6] Issuing client B realtime ticket..."
    )

    ticket_b = await asyncio.to_thread(
        create_ticket,
        api_base=api_base,
        workspace_id=workspace_id,
        channel_id=channel_id,
        token=token_b,
    )

    print(
        "PASS: Client B ticket issued"
    )

    url_a = websocket_url(
        ws_base=ws_base,
        ws_path=ws_path,
        workspace_id=workspace_id,
        channel_id=channel_id,
        ticket=ticket_a,
    )

    url_b = websocket_url(
        ws_base=ws_base,
        ws_path=ws_path,
        workspace_id=workspace_id,
        channel_id=channel_id,
        ticket=ticket_b,
    )

    print()
    print(
        "[3/6] Connecting authenticated client A..."
    )

    async with websockets.connect(
        url_a,
        open_timeout=timeout_seconds,
        close_timeout=5,
        ping_interval=None,
    ) as socket_a:
        print(
            "PASS: Client A connected"
        )

        print()
        print(
            "[4/6] Connecting authenticated client B..."
        )

        async with websockets.connect(
            url_b,
            open_timeout=timeout_seconds,
            close_timeout=5,
            ping_interval=None,
        ) as socket_b:
            print(
                "PASS: Client B connected"
            )

            print()
            print(
                "[5/6] Creating channel message "
                "as client A..."
            )

            unique_marker = (
                "phase16d-runtime-"
                + str(
                    int(
                        time.time()
                        * 1000
                    )
                )
                + "-"
                + uuid.uuid4().hex[:8]
            )

            created = await asyncio.to_thread(
                send_message,
                api_base=api_base,
                channel_id=channel_id,
                token=token_a,
                content=unique_marker,
            )

            message_id = str(
                created[
                    "id"
                ]
            )

            print(
                "PASS: Message created"
            )
            print(
                f"Message ID: {message_id}"
            )

            print()
            print(
                "[6/6] Waiting for client B "
                "realtime fanout..."
            )

            event = await wait_for_message_event(
                socket_b,
                message_id=message_id,
                timeout_seconds=timeout_seconds,
            )

            received_type = (
                event_type(
                    event
                )
                or "<unknown>"
            )

            received_message_id = (
                extract_message_id(
                    event
                )
            )

            print(
                "PASS: Client B received "
                "realtime message event"
            )
            print(
                f"Event type: {received_type}"
            )

            if received_message_id:
                print(
                    "Realtime message ID: "
                    f"{received_message_id}"
                )

            if (
                received_message_id
                and received_message_id
                != message_id
            ):
                fail(
                    "Realtime message ID does not "
                    "match HTTP-created message."
                )

    print()
    print(
        "=" * 49
    )
    print(
        " PHASE 16D TWO-CLIENT "
        "MESSAGE FANOUT PASS"
    )
    print(
        "=" * 49
    )


def main() -> None:
    try:
        asyncio.run(
            main_async()
        )

    except GateFailure as exc:
        print(
            f"FAIL: {exc}"
        )
        raise

    except Exception as exc:
        print(
            f"FAIL: {exc}"
        )
        raise


if __name__ == "__main__":
    main()