from __future__ import annotations

import inspect
import sys
from pathlib import Path
from typing import Any


BACKEND_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)


backend_root_text = str(
    BACKEND_ROOT
)


if (
    backend_root_text
    not in sys.path
):
    sys.path.insert(
        0,
        backend_root_text,
    )


def print_callable_contract(
    *,
    owner_name: str,
    name: str,
    value: Any,
) -> None:
    if not callable(
        value
    ):
        return

    try:
        signature = (
            inspect.signature(
                value
            )
        )

    except (
        TypeError,
        ValueError,
    ):
        signature = (
            "<unavailable>"
        )

    print(
        f"{owner_name}."
        f"{name}"
        f"{signature}"
    )


def main() -> int:
    print("")
    print(
        "================================================="
    )
    print(
        " PYTHON IMPORT ROOT"
    )
    print(
        "================================================="
    )

    print(
        BACKEND_ROOT
    )

    from app.modules.channels import (
        realtime_events,
    )

    from app.modules.channels.realtime_events import (
        WorkspaceChannelRealtimeEventPublisher,
        channel_realtime_events,
    )

    print("")
    print(
        "================================================="
    )
    print(
        " REALTIME MODULE"
    )
    print(
        "================================================="
    )

    print(
        realtime_events.__file__
    )

    print("")
    print(
        "================================================="
    )
    print(
        " PUBLISHER CLASS"
    )
    print(
        "================================================="
    )

    print(
        WorkspaceChannelRealtimeEventPublisher
    )

    print("")
    print(
        "================================================="
    )
    print(
        " PUBLISHER CLASS CALLABLES"
    )
    print(
        "================================================="
    )

    for name in sorted(
        dir(
            WorkspaceChannelRealtimeEventPublisher
        )
    ):
        if name.startswith(
            "_"
        ):
            continue

        value = getattr(
            WorkspaceChannelRealtimeEventPublisher,
            name,
        )

        print_callable_contract(
            owner_name=(
                "WorkspaceChannelRealtimeEventPublisher"
            ),
            name=name,
            value=value,
        )

    print("")
    print(
        "================================================="
    )
    print(
        " PUBLISHER INSTANCE"
    )
    print(
        "================================================="
    )

    print(
        "type:",
        type(
            channel_realtime_events
        ),
    )

    print(
        "repr:",
        repr(
            channel_realtime_events
        ),
    )

    print("")
    print(
        "================================================="
    )
    print(
        " INSTANCE CALLABLES"
    )
    print(
        "================================================="
    )

    for name in sorted(
        dir(
            channel_realtime_events
        )
    ):
        if name.startswith(
            "_"
        ):
            continue

        value = getattr(
            channel_realtime_events,
            name,
        )

        print_callable_contract(
            owner_name=(
                "channel_realtime_events"
            ),
            name=name,
            value=value,
        )

    print("")
    print(
        "================================================="
    )
    print(
        " MODULE REALTIME SYMBOLS"
    )
    print(
        "================================================="
    )

    interesting_terms = (
        "publish",
        "event",
        "realtime",
        "message",
        "channel",
        "sequence",
        "replay",
    )

    for name in sorted(
        dir(
            realtime_events
        )
    ):
        if name.startswith(
            "_"
        ):
            continue

        lowered = (
            name.lower()
        )

        if not any(
            term in lowered
            for term in interesting_terms
        ):
            continue

        value = getattr(
            realtime_events,
            name,
        )

        if callable(
            value
        ):
            print_callable_contract(
                owner_name=(
                    "realtime_events"
                ),
                name=name,
                value=value,
            )

        else:
            print(
                f"realtime_events."
                f"{name}: "
                f"{type(value).__name__}"
            )

    print("")
    print(
        "================================================="
    )
    print(
        " CONTRACT PROBE PASS"
    )
    print(
        "================================================="
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )