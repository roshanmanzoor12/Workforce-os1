from __future__ import annotations

import pytest

from app.modules.channels.realtime_replay import (
    ChannelRealtimeReplayPolicy,
    ReplayWindowExceeded,
)


def make_policy(
) -> ChannelRealtimeReplayPolicy:
    return ChannelRealtimeReplayPolicy(
        batch_size=200,
        max_events=1000,
    )


def test_replay_accepts_normal_window() -> None:
    policy = make_policy()

    result = policy.validate(
        after_sequence=100,
        current_sequence=150,
        requested_limit=100,
    )

    assert result == 100


def test_replay_clamps_requested_limit() -> None:
    policy = make_policy()

    result = policy.validate(
        after_sequence=100,
        current_sequence=500,
        requested_limit=900,
    )

    assert result == 200


def test_replay_rejects_negative_cursor() -> None:
    policy = make_policy()

    with pytest.raises(
        ReplayWindowExceeded
    ):
        policy.validate(
            after_sequence=-1,
            current_sequence=10,
            requested_limit=10,
        )


def test_replay_rejects_future_cursor() -> None:
    policy = make_policy()

    with pytest.raises(
        ReplayWindowExceeded
    ):
        policy.validate(
            after_sequence=101,
            current_sequence=100,
            requested_limit=10,
        )


def test_replay_rejects_unbounded_history() -> None:
    policy = make_policy()

    with pytest.raises(
        ReplayWindowExceeded
    ):
        policy.validate(
            after_sequence=1,
            current_sequence=2000,
            requested_limit=100,
        )


def test_replay_rejects_zero_limit() -> None:
    policy = make_policy()

    with pytest.raises(
        ReplayWindowExceeded
    ):
        policy.validate(
            after_sequence=1,
            current_sequence=2,
            requested_limit=0,
        )