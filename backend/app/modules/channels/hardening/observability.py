from __future__ import annotations

import logging
import time
from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass
from threading import Lock
from typing import (
    Any,
    Iterator,
)


logger = logging.getLogger(
    "workforce.channels.realtime"
)


@dataclass(
    frozen=True,
    slots=True,
)
class ChannelRealtimeMetricSnapshot:
    counters: dict[str, int]


class ChannelRealtimeMetrics:
    """
    Lightweight process-local realtime counters plus structured logging.

    This intentionally does not force a Prometheus/OpenTelemetry
    dependency.  Phase 17 can later export these counters to the platform
    metrics backend without changing realtime business logic.
    """

    def __init__(
        self,
    ) -> None:
        self._lock = Lock()
        self._counters: Counter[str] = (
            Counter()
        )

    def increment(
        self,
        name: str,
        amount: int = 1,
    ) -> None:
        if amount < 0:
            raise ValueError(
                "Metric increment cannot be negative."
            )

        with self._lock:
            self._counters[
                name
            ] += amount

    def snapshot(
        self,
    ) -> ChannelRealtimeMetricSnapshot:
        with self._lock:
            values = dict(
                self._counters
            )

        return ChannelRealtimeMetricSnapshot(
            counters=values
        )

    def reset(
        self,
    ) -> None:
        with self._lock:
            self._counters.clear()

    def log_event(
        self,
        *,
        event: str,
        workspace_id: object | None = None,
        channel_id: object | None = None,
        user_id: object | None = None,
        connection_id: object | None = None,
        sequence: object | None = None,
        extra: dict[str, Any] | None = None,
        level: int = logging.INFO,
    ) -> None:
        payload: dict[str, Any] = {
            "event":
                event,

            "workspace_id":
                (
                    str(
                        workspace_id
                    )
                    if workspace_id is not None
                    else None
                ),

            "channel_id":
                (
                    str(
                        channel_id
                    )
                    if channel_id is not None
                    else None
                ),

            "user_id":
                (
                    str(
                        user_id
                    )
                    if user_id is not None
                    else None
                ),

            "connection_id":
                (
                    str(
                        connection_id
                    )
                    if connection_id is not None
                    else None
                ),

            "sequence":
                sequence,
        }

        if extra:
            payload.update(
                extra
            )

        logger.log(
            level,
            "channel_realtime_event",
            extra={
                "channel_realtime":
                    payload,
            },
        )

    @contextmanager
    def measure(
        self,
        operation: str,
        *,
        workspace_id: object | None = None,
        channel_id: object | None = None,
    ) -> Iterator[None]:
        started = (
            time.perf_counter()
        )

        self.increment(
            f"{operation}.started"
        )

        try:
            yield

        except Exception:
            self.increment(
                f"{operation}.failed"
            )

            elapsed_ms = (
                time.perf_counter()
                -
                started
            ) * 1000.0

            logger.exception(
                "channel_realtime_operation_failed",
                extra={
                    "channel_realtime": {
                        "operation":
                            operation,

                        "workspace_id":
                            (
                                str(
                                    workspace_id
                                )
                                if workspace_id is not None
                                else None
                            ),

                        "channel_id":
                            (
                                str(
                                    channel_id
                                )
                                if channel_id is not None
                                else None
                            ),

                        "elapsed_ms":
                            round(
                                elapsed_ms,
                                3,
                            ),
                    }
                },
            )

            raise

        else:
            self.increment(
                f"{operation}.completed"
            )

            elapsed_ms = (
                time.perf_counter()
                -
                started
            ) * 1000.0

            logger.debug(
                "channel_realtime_operation_completed",
                extra={
                    "channel_realtime": {
                        "operation":
                            operation,

                        "workspace_id":
                            (
                                str(
                                    workspace_id
                                )
                                if workspace_id is not None
                                else None
                            ),

                        "channel_id":
                            (
                                str(
                                    channel_id
                                )
                                if channel_id is not None
                                else None
                            ),

                        "elapsed_ms":
                            round(
                                elapsed_ms,
                                3,
                            ),
                    }
                },
            )


channel_realtime_metrics = (
    ChannelRealtimeMetrics()
)