from __future__ import annotations


class ReplayWindowExceeded(
    ValueError
):
    pass


class ChannelRealtimeReplayPolicy:
    """
    Bounds reconnect replay work.

    A reconnect may request only a bounded batch and may not ask the
    server to recover an arbitrarily old sequence window.

    When max_events is exceeded the client must perform its canonical
    HTTP refresh rather than forcing an unbounded Redis replay.
    """

    def __init__(
        self,
        *,
        batch_size: int,
        max_events: int,
    ) -> None:
        if batch_size <= 0:
            raise ValueError(
                "batch_size must be positive."
            )

        if max_events <= 0:
            raise ValueError(
                "max_events must be positive."
            )

        if batch_size > max_events:
            raise ValueError(
                "batch_size cannot exceed "
                "max_events."
            )

        self.batch_size = batch_size
        self.max_events = max_events

    def validate(
        self,
        *,
        after_sequence: int,
        current_sequence: int,
        requested_limit: int,
    ) -> int:
        if after_sequence < 0:
            raise ReplayWindowExceeded(
                "after_sequence cannot "
                "be negative."
            )

        if current_sequence < 0:
            raise ReplayWindowExceeded(
                "current sequence cannot "
                "be negative."
            )

        if requested_limit <= 0:
            raise ReplayWindowExceeded(
                "Replay limit must "
                "be positive."
            )

        if (
            after_sequence
            > current_sequence
        ):
            raise ReplayWindowExceeded(
                "Replay cursor is ahead "
                "of the current sequence."
            )

        gap = (
            current_sequence
            - after_sequence
        )

        if gap > self.max_events:
            raise ReplayWindowExceeded(
                "Realtime replay window "
                "was exceeded. Perform "
                "a canonical channel refresh."
            )

        return min(
            requested_limit,
            self.batch_size,
            self.max_events,
        )


__all__ = [
    "ChannelRealtimeReplayPolicy",
    "ReplayWindowExceeded",
]