from __future__ import annotations

import inspect
import sys

from phase16d_common import (
    choose_channel_ws_path,
    discover_fastapi_routes,
    fail,
)


def main() -> int:
    print()
    print(
        "================================================="
    )
    print(
        " WorkforceOS Phase 16D Runtime Contract Probe"
    )
    print(
        "================================================="
    )
    print()

    discovery = (
        discover_fastapi_routes()
    )

    print(
        "WebSocket routes:"
    )

    for path in (
        discovery.websocket_paths
    ):
        print(
            f"  {path}"
        )

    print()

    selected = (
        choose_channel_ws_path()
    )

    print(
        "Selected channel realtime route:"
    )
    print(
        f"  {selected}"
    )
    print()

    try:
        from app.modules.channels.realtime_bus import (
            channel_realtime_bus,
        )
    except Exception as exc:
        fail(
            f"Unable to import channel_realtime_bus: {exc}"
        )

    try:
        from app.modules.channels.realtime_events import (
            channel_realtime_events,
        )
    except Exception as exc:
        fail(
            f"Unable to import channel_realtime_events: {exc}"
        )

    replay_method = getattr(
        channel_realtime_bus,
        "replay",
        None,
    )

    if replay_method is None:
        fail(
            "channel_realtime_bus.replay missing."
        )

    print(
        "Replay signature:"
    )
    print(
        inspect.signature(
            replay_method
        )
    )
    print()

    attachment_method = getattr(
        channel_realtime_events,
        "attachment_bound",
        None,
    )

    if attachment_method is None:
        fail(
            "attachment_bound publisher missing."
        )

    print(
        "Attachment publisher:"
    )
    print(
        inspect.signature(
            attachment_method
        )
    )
    print()

    print(
        "PASS: websocket route discovery"
    )
    print(
        "PASS: replay contract"
    )
    print(
        "PASS: attachment publisher"
    )
    print()
    print(
        "================================================="
    )
    print(
        " PHASE 16D CONTRACT PROBE PASS"
    )
    print(
        "================================================="
    )
    print()

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(
            main()
        )
    except Exception as exc:
        print(
            f"FAIL: {exc}",
            file=sys.stderr,
        )
        raise