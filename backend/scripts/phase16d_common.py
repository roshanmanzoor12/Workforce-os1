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
from dataclasses import dataclass
from typing import Any


class GateFailure(RuntimeError):
    pass


def fail(message: str) -> None:
    raise GateFailure(message)


def env(
    name: str,
    *,
    required: bool = True,
    default: str | None = None,
) -> str:
    value = os.getenv(name)

    if value is None:
        value = default

    if value is None:
        value = ""

    value = value.strip()

    if required and not value:
        fail(
            f"Required environment variable is missing: {name}"
        )

    return value


def api_base() -> str:
    return env(
        "WF_API_BASE",
        default="http://127.0.0.1:8000/api/v1",
    ).rstrip("/")


def ws_base() -> str:
    return env(
        "WF_WS_BASE",
        default="ws://127.0.0.1:8000",
    ).rstrip("/")


def timeout_seconds() -> float:
    raw = env(
        "WF_WS_TIMEOUT_SECONDS",
        required=False,
        default="12",
    )

    try:
        return max(
            3.0,
            float(raw),
        )
    except ValueError:
        return 12.0


def replay_timeout_seconds() -> float:
    raw = env(
        "WF_REPLAY_TIMEOUT_SECONDS",
        required=False,
        default="15",
    )

    try:
        return max(
            3.0,
            float(raw),
        )
    except ValueError:
        return 15.0


def token_a() -> str:
    return env(
        "WF_TOKEN_A",
    )


def token_b() -> str:
    return env(
        "WF_TOKEN_B",
    )


def workspace_id() -> str:
    return str(
        uuid.UUID(
            env(
                "WF_WORKSPACE_ID",
            )
        )
    )


def channel_id() -> str:
    return str(
        uuid.UUID(
            env(
                "WF_CHANNEL_ID",
            )
        )
    )


def optional_message_id() -> str | None:
    value = env(
        "WF_MESSAGE_ID",
        required=False,
        default="",
    )

    if not value:
        return None

    return str(
        uuid.UUID(
            value
        )
    )


def _headers(
    token: str | None,
    *,
    content_type: str | None = "application/json",
) -> dict[str, str]:
    headers: dict[str, str] = {
        "Accept": "application/json",
    }

    if content_type:
        headers[
            "Content-Type"
        ] = content_type

    if token:
        headers[
            "Authorization"
        ] = f"Bearer {token}"

    return headers


def http_json(
    method: str,
    path: str,
    *,
    token: str | None = None,
    payload: Any = None,
    expected: set[int] | None = None,
) -> tuple[int, Any]:
    url = (
        path
        if path.startswith(
            ("http://", "https://")
        )
        else f"{api_base()}/{path.lstrip('/')}"
    )

    data: bytes | None = None

    if payload is not None:
        data = json.dumps(
            payload,
        ).encode(
            "utf-8"
        )

    request = urllib.request.Request(
        url=url,
        data=data,
        method=method.upper(),
        headers=_headers(
            token,
        ),
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=timeout_seconds(),
        ) as response:
            body = response.read()

            status = int(
                response.status
            )

    except urllib.error.HTTPError as exc:
        status = int(
            exc.code
        )

        body = exc.read()

    except urllib.error.URLError as exc:
        fail(
            f"HTTP request failed for {url}: {exc}"
        )

    decoded: Any = None

    if body:
        text = body.decode(
            "utf-8",
            errors="replace",
        )

        try:
            decoded = json.loads(
                text
            )
        except json.JSONDecodeError:
            decoded = text

    if (
        expected is not None
        and status not in expected
    ):
        fail(
            f"{method.upper()} {url} returned "
            f"{status}, expected {sorted(expected)}. "
            f"Body={decoded!r}"
        )

    return status, decoded


def extract_id(
    value: Any,
    *names: str,
) -> str:
    if not isinstance(
        value,
        dict,
    ):
        fail(
            f"Expected object while extracting ID, got {type(value).__name__}"
        )

    for name in names:
        candidate = value.get(
            name
        )

        if candidate:
            return str(
                candidate
            )

    fail(
        f"Unable to extract any ID field from: {names}"
    )


def event_type(
    event: Any,
) -> str:
    if not isinstance(
        event,
        dict,
    ):
        return ""

    value = event.get(
        "event_type"
    )

    return (
        value
        if isinstance(
            value,
            str,
        )
        else ""
    )


def event_sequence(
    event: Any,
) -> int:
    if not isinstance(
        event,
        dict,
    ):
        return 0

    value = event.get(
        "sequence"
    )

    if isinstance(
        value,
        int,
    ):
        return value

    if isinstance(
        value,
        str,
    ):
        try:
            return int(
                value
            )
        except ValueError:
            return 0

    return 0


def event_payload(
    event: Any,
) -> dict[str, Any]:
    if not isinstance(
        event,
        dict,
    ):
        return {}

    value = event.get(
        "payload"
    )

    return (
        value
        if isinstance(
            value,
            dict,
        )
        else {}
    )


def event_matches_message(
    event: Any,
    message_id: str,
) -> bool:
    payload = event_payload(
        event
    )

    candidate = payload.get(
        "message_id"
    )

    if candidate is None:
        message = payload.get(
            "message"
        )

        if isinstance(
            message,
            dict,
        ):
            candidate = message.get(
                "id"
            )

    return str(
        candidate or ""
    ) == str(
        message_id
    )


@dataclass(slots=True)
class RouteDiscovery:
    websocket_paths: list[str]
    channel_realtime_paths: list[str]


def discover_fastapi_routes() -> RouteDiscovery:
    backend_root = os.path.abspath(
        os.path.join(
            os.path.dirname(
                __file__
            ),
            "..",
        )
    )

    if backend_root not in sys.path:
        sys.path.insert(
            0,
            backend_root,
        )

    try:
        from app.main import app
    except Exception as exc:
        fail(
            f"Unable to import app.main.app: {exc}"
        )

    websocket_paths: list[str] = []
    channel_realtime_paths: list[str] = []

    def walk_router(
        router,
        *,
        prefix: str = "",
    ) -> None:
        routes = getattr(
            router,
            "routes",
            [],
        )

        for route in routes:
            route_type_name = (
                type(route).__name__
            )

            if (
                route_type_name
                == "_IncludedRouter"
            ):
                include_context = getattr(
                    route,
                    "include_context",
                    None,
                )

                child_prefix = ""

                if include_context is not None:
                    child_prefix = str(
                        getattr(
                            include_context,
                            "prefix",
                            "",
                        )
                        or ""
                    )

                original_router = getattr(
                    route,
                    "original_router",
                    None,
                )

                if original_router is not None:
                    walk_router(
                        original_router,
                        prefix=(
                            prefix
                            + child_prefix
                        ),
                    )

                continue

            path = str(
                getattr(
                    route,
                    "path",
                    "",
                )
                or ""
            )

            if not path:
                continue

            full_path = (
                prefix
                + path
            )

            route_type = (
                route_type_name.lower()
            )

            is_websocket = (
                "websocket"
                in route_type
            )

            if not is_websocket:
                continue

            websocket_paths.append(
                full_path
            )

            lowered = (
                full_path.lower()
            )

            if (
                "channel" in lowered
                or "workspace" in lowered
            ):
                channel_realtime_paths.append(
                    full_path
                )

    walk_router(
        app.router
    )

    return RouteDiscovery(
        websocket_paths=sorted(
            set(
                websocket_paths
            )
        ),
        channel_realtime_paths=sorted(
            set(
                channel_realtime_paths
            )
        ),
    )


def choose_channel_ws_path() -> str:
    override = env(
        "WF_CHANNEL_WS_PATH",
        required=False,
        default="",
    )

    if override:
        return override

    discovered = (
        discover_fastapi_routes()
    )

    candidates = (
        discovered.channel_realtime_paths
        or discovered.websocket_paths
    )

    if len(
        candidates
    ) != 1:
        fail(
            "Unable to select one channel websocket route automatically. "
            f"Candidates={candidates}. "
            "Set WF_CHANNEL_WS_PATH in phase16d_runtime_env.ps1."
        )

    return candidates[
        0
    ]


def build_ws_url(
    *,
    path: str,
    workspace: str,
    channel: str,
    token: str | None,
    after_sequence: int | None = None,
) -> str:
    replacements = {
        "workspace_id":
            workspace,
        "channel_id":
            channel,
    }

    rendered = path

    for key, value in replacements.items():
        rendered = rendered.replace(
            "{" + key + "}",
            urllib.parse.quote(
                value,
                safe="",
            ),
        )

    query: dict[str, str] = {}

    if token:
        query[
            "token"
        ] = token

    if (
        after_sequence
        is not None
    ):
        query[
            "after_sequence"
        ] = str(
            after_sequence
        )

    encoded = urllib.parse.urlencode(
        query
    )

    suffix = (
        f"?{encoded}"
        if encoded
        else ""
    )

    return (
        f"{ws_base()}{rendered}{suffix}"
    )


async def receive_until(
    websocket: Any,
    predicate: Any,
    *,
    timeout: float | None = None,
) -> dict[str, Any]:
    deadline = (
        time.monotonic()
        +
        (
            timeout
            if timeout is not None
            else timeout_seconds()
        )
    )

    while True:
        remaining = (
            deadline
            -
            time.monotonic()
        )

        if remaining <= 0:
            fail(
                "Timed out waiting for matching realtime event."
            )

        raw = await asyncio.wait_for(
            websocket.recv(),
            timeout=remaining,
        )

        if isinstance(
            raw,
            bytes,
        ):
            raw = raw.decode(
                "utf-8",
                errors="replace",
            )

        try:
            event = json.loads(
                raw
            )
        except json.JSONDecodeError:
            continue

        if predicate(
            event
        ):
            return event