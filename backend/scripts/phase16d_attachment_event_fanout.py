from __future__ import annotations

import asyncio
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any

import websockets


# =====================================================================
# PATH SETUP
# =====================================================================


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


# =====================================================================
# ERRORS
# =====================================================================


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


# =====================================================================
# OUTPUT
# =====================================================================


def heading(
    text: str,
) -> None:
    print()
    print(
        "=" * 57
    )
    print(
        f" {text}"
    )
    print(
        "=" * 57
    )
    print()


# =====================================================================
# ENVIRONMENT
# =====================================================================


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


# =====================================================================
# HTTP
# =====================================================================


def http_json(
    *,
    method: str,
    url: str,
    token: str | None = None,
    body: dict[str, Any] | None = None,
    timeout: float = 20.0,
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
                    "utf-8",
                    errors="replace",
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
            f"{method} {url}: {exc}"
        ) from exc


# =====================================================================
# RAW OBJECT UPLOAD
# =====================================================================


def upload_raw_file(
    *,
    upload_url: str,
    content: bytes,
    content_type: str,
    timeout: float = 20.0,
) -> None:
    request = urllib.request.Request(
        url=upload_url,
        data=content,
        headers={
            "Content-Type": content_type,
        },
        method="PUT",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=timeout,
        ) as response:
            status_code = int(
                response.status
            )

            if (
                status_code < 200
                or status_code >= 300
            ):
                fail(
                    "Attachment upload returned "
                    f"HTTP {status_code}."
                )

    except urllib.error.HTTPError as exc:
        raw = (
            exc.read()
            .decode(
                "utf-8",
                errors="replace",
            )
        )

        raise GateFailure(
            "Attachment object upload failed: "
            f"HTTP {exc.code}: {raw}"
        ) from exc

    except urllib.error.URLError as exc:
        raise GateFailure(
            "Attachment object upload "
            f"connection failed: {exc}"
        ) from exc


# =====================================================================
# REALTIME TICKET
# =====================================================================


def create_ticket(
    *,
    api_base: str,
    workspace_id: str,
    channel_id: str,
    token: str,
) -> str:
    url = (
        f"{api_base.rstrip('/')}"
        f"/workspaces/"
        f"{workspace_id}"
        f"/channels/"
        f"{channel_id}"
        f"/realtime/ticket"
    )

    status_code, data = http_json(
        method="POST",
        url=url,
        token=token,
    )

    if status_code != 200:
        fail(
            "Realtime ticket endpoint "
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

    return ticket


# =====================================================================
# WEBSOCKET URL
# =====================================================================


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


# =====================================================================
# MESSAGE
# =====================================================================


def create_message(
    *,
    api_base: str,
    channel_id: str,
    token: str,
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
            "content": (
                "Phase 16D runtime attachment "
                f"fanout {uuid.uuid4().hex[:10]}"
            ),
        },
    )

    if status_code != 201:
        fail(
            "Message creation returned "
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


# =====================================================================
# ATTACHMENT PREPARE
# =====================================================================


def prepare_attachment(
    *,
    api_base: str,
    channel_id: str,
    token: str,
    content: bytes,
) -> dict[str, Any]:
    url = (
        f"{api_base.rstrip('/')}"
        "/attachments/prepare"
    )

    status_code, data = http_json(
        method="POST",
        url=url,
        token=token,
        body={
            "scope": "CHANNEL",
            "conversation_id": None,
            "channel_id": channel_id,
            "filename": (
                "phase16d-runtime-attachment.txt"
            ),
            "content_type": "text/plain",
            "size_bytes": len(
                content
            ),
        },
    )

    if status_code != 201:
        fail(
            "Attachment prepare returned "
            f"HTTP {status_code}."
        )

    if not isinstance(
        data,
        dict,
    ):
        fail(
            "Attachment prepare response "
            "was not a JSON object."
        )

    attachment_id = str(
        data.get(
            "attachment_id",
            "",
        )
        or ""
    ).strip()

    upload_url = str(
        data.get(
            "upload_url",
            "",
        )
        or ""
    ).strip()

    if not attachment_id:
        fail(
            "Attachment prepare response "
            "did not contain attachment_id."
        )

    if not upload_url:
        fail(
            "Attachment prepare response "
            "did not contain upload_url."
        )

    return data


# =====================================================================
# ATTACHMENT COMPLETE
# =====================================================================


def complete_attachment(
    *,
    api_base: str,
    attachment_id: str,
    token: str,
) -> dict[str, Any]:
    url = (
        f"{api_base.rstrip('/')}"
        f"/attachments/"
        f"{attachment_id}"
        f"/complete"
    )

    status_code, data = http_json(
        method="POST",
        url=url,
        token=token,
        body={
            "checksum_sha256": None,
        },
    )

    if status_code != 200:
        fail(
            "Attachment completion returned "
            f"HTTP {status_code}."
        )

    if not isinstance(
        data,
        dict,
    ):
        fail(
            "Attachment completion response "
            "was not a JSON object."
        )

    return data


# =====================================================================
# ATTACHMENT BIND
# =====================================================================


def bind_attachment(
    *,
    api_base: str,
    channel_id: str,
    message_id: str,
    attachment_id: str,
    token: str,
) -> Any:
    url = (
        f"{api_base.rstrip('/')}"
        f"/workspace-channels/"
        f"{channel_id}"
        f"/messages/"
        f"{message_id}"
        f"/attachments"
    )

    status_code, data = http_json(
        method="POST",
        url=url,
        token=token,
        body={
            "attachment_ids": [
                attachment_id,
            ],
        },
    )

    if (
        status_code < 200
        or status_code >= 300
    ):
        fail(
            "Attachment binding returned "
            f"HTTP {status_code}."
        )

    return data


# =====================================================================
# EVENT HELPERS
# =====================================================================


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


def event_payload(
    event: dict[str, Any],
) -> dict[str, Any]:
    payload = event.get(
        "payload"
    )

    if isinstance(
        payload,
        dict,
    ):
        return payload

    return {}


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

    payload = event_payload(
        event
    )

    value = payload.get(
        "message_id"
    )

    if value is not None:
        return str(
            value
        )

    return ""


def extract_attachment_ids(
    event: dict[str, Any],
) -> list[str]:
    direct = event.get(
        "attachment_ids"
    )

    if isinstance(
        direct,
        list,
    ):
        return [
            str(
                item
            )
            for item in direct
        ]

    payload = event_payload(
        event
    )

    value = payload.get(
        "attachment_ids"
    )

    if isinstance(
        value,
        list,
    ):
        return [
            str(
                item
            )
            for item in value
        ]

    return []


# =====================================================================
# WAIT FOR ATTACHMENT EVENT
# =====================================================================


async def wait_for_attachment_bound(
    websocket,
    *,
    message_id: str,
    attachment_id: str,
    timeout_seconds: float,
) -> dict[str, Any]:
    loop = (
        asyncio.get_running_loop()
    )

    deadline = (
        loop.time()
        + timeout_seconds
    )

    observed_types: list[str] = []

    while True:
        remaining = (
            deadline
            - loop.time()
        )

        if remaining <= 0:
            fail(
                "Timed out waiting for "
                "channel.attachment.bound. "
                f"Observed={observed_types}"
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
            observed_types.append(
                kind
            )

        if (
            kind
            != "channel.attachment.bound"
        ):
            continue

        received_message_id = (
            extract_message_id(
                event
            )
        )

        received_attachment_ids = (
            extract_attachment_ids(
                event
            )
        )

        if (
            received_message_id
            != message_id
        ):
            continue

        if (
            attachment_id
            not in received_attachment_ids
        ):
            continue

        return event


# =====================================================================
# MAIN
# =====================================================================


async def main_async() -> None:
    heading(
        "WorkforceOS Phase 16D "
        "Attachment Event Fanout"
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

    # ---------------------------------------------------------
    # Validate UUID environment
    # ---------------------------------------------------------

    try:
        uuid.UUID(
            workspace_id
        )

        uuid.UUID(
            channel_id
        )

    except ValueError as exc:
        fail(
            "WF_WORKSPACE_ID / WF_CHANNEL_ID "
            "must be valid UUID values."
        )

    # ---------------------------------------------------------
    # Ticket
    # ---------------------------------------------------------

    print(
        "[1/8] Issuing receiver realtime ticket..."
    )

    ticket_b = await asyncio.to_thread(
        create_ticket,
        api_base=api_base,
        workspace_id=workspace_id,
        channel_id=channel_id,
        token=token_b,
    )

    print(
        "PASS: Receiver ticket issued"
    )

    socket_url = websocket_url(
        ws_base=ws_base,
        ws_path=ws_path,
        workspace_id=workspace_id,
        channel_id=channel_id,
        ticket=ticket_b,
    )

    # ---------------------------------------------------------
    # Socket
    # ---------------------------------------------------------

    print()
    print(
        "[2/8] Connecting receiver WebSocket..."
    )

    async with websockets.connect(
        socket_url,
        open_timeout=timeout_seconds,
        close_timeout=5,
        ping_interval=None,
    ) as socket_b:
        print(
            "PASS: Receiver connected"
        )

        # -----------------------------------------------------
        # Message
        # -----------------------------------------------------

        print()
        print(
            "[3/8] Creating channel message..."
        )

        message = await asyncio.to_thread(
            create_message,
            api_base=api_base,
            channel_id=channel_id,
            token=token_a,
        )

        message_id = str(
            message[
                "id"
            ]
        )

        print(
            "PASS: Message created"
        )
        print(
            f"Message ID: {message_id}"
        )

        # -----------------------------------------------------
        # Prepare
        # -----------------------------------------------------

        attachment_content = (
            b"WorkforceOS Phase 16D "
            b"runtime attachment fanout.\n"
        )

        print()
        print(
            "[4/8] Preparing channel attachment..."
        )

        prepared = await asyncio.to_thread(
            prepare_attachment,
            api_base=api_base,
            channel_id=channel_id,
            token=token_a,
            content=attachment_content,
        )

        attachment_id = str(
            prepared[
                "attachment_id"
            ]
        )

        upload_url = str(
            prepared[
                "upload_url"
            ]
        )

        print(
            "PASS: Attachment prepared"
        )
        print(
            f"Attachment ID: {attachment_id}"
        )

        # -----------------------------------------------------
        # Upload
        # -----------------------------------------------------

        print()
        print(
            "[5/8] Uploading attachment object..."
        )

        await asyncio.to_thread(
            upload_raw_file,
            upload_url=upload_url,
            content=attachment_content,
            content_type="text/plain",
        )

        print(
            "PASS: Attachment object uploaded"
        )

        # -----------------------------------------------------
        # Complete
        # -----------------------------------------------------

        print()
        print(
            "[6/8] Completing attachment..."
        )

        await asyncio.to_thread(
            complete_attachment,
            api_base=api_base,
            attachment_id=attachment_id,
            token=token_a,
        )

        print(
            "PASS: Attachment READY"
        )

        # -----------------------------------------------------
        # Bind
        # -----------------------------------------------------

        print()
        print(
            "[7/8] Binding attachment to message..."
        )

        await asyncio.to_thread(
            bind_attachment,
            api_base=api_base,
            channel_id=channel_id,
            message_id=message_id,
            attachment_id=attachment_id,
            token=token_a,
        )

        print(
            "PASS: Attachment binding HTTP mutation"
        )

        # -----------------------------------------------------
        # Realtime
        # -----------------------------------------------------

        print()
        print(
            "[8/8] Waiting for "
            "channel.attachment.bound..."
        )

        event = await wait_for_attachment_bound(
            socket_b,
            message_id=message_id,
            attachment_id=attachment_id,
            timeout_seconds=timeout_seconds,
        )

        received_type = (
            event_type(
                event
            )
        )

        received_message_id = (
            extract_message_id(
                event
            )
        )

        received_attachment_ids = (
            extract_attachment_ids(
                event
            )
        )

        print(
            "PASS: Receiver received "
            "channel.attachment.bound"
        )

        print(
            f"Event type: {received_type}"
        )

        print(
            "Realtime message ID: "
            f"{received_message_id}"
        )

        print(
            "Realtime attachment IDs: "
            + ", ".join(
                received_attachment_ids
            )
        )

        if (
            received_type
            != "channel.attachment.bound"
        ):
            fail(
                "Unexpected realtime event type."
            )

        if (
            received_message_id
            != message_id
        ):
            fail(
                "Realtime attachment event "
                "message ID mismatch."
            )

        if (
            attachment_id
            not in received_attachment_ids
        ):
            fail(
                "Realtime event did not contain "
                "the bound attachment ID."
            )

    print()
    print(
        "=" * 57
    )
    print(
        " PHASE 16D ATTACHMENT EVENT FANOUT PASS"
    )
    print(
        "=" * 57
    )


# =====================================================================
# ENTRYPOINT
# =====================================================================


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