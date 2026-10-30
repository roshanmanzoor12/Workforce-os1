from __future__ import annotations

import uuid

import pytest

from app.modules.friends.enums import (
    FriendshipStatus,
)
from app.modules.friends.repository import (
    normalize_user_pair,
)


def test_friendship_status_values():
    assert (
        FriendshipStatus.PENDING.value
        == "pending"
    )

    assert (
        FriendshipStatus.ACCEPTED.value
        == "accepted"
    )

    assert (
        FriendshipStatus.BLOCKED.value
        == "blocked"
    )


def test_user_pair_is_deterministic():
    first = uuid.UUID(
        "00000000-0000-0000-0000-000000000002"
    )

    second = uuid.UUID(
        "00000000-0000-0000-0000-000000000001"
    )

    low, high = normalize_user_pair(
        first,
        second,
    )

    assert low == second
    assert high == first


def test_pair_normalization_same_in_reverse():
    first = uuid.uuid4()
    second = uuid.uuid4()

    one = normalize_user_pair(
        first,
        second,
    )

    two = normalize_user_pair(
        second,
        first,
    )

    assert one == two


def test_self_friendship_rejected():
    user_id = uuid.uuid4()

    with pytest.raises(
        ValueError,
        match="themselves",
    ):
        normalize_user_pair(
            user_id,
            user_id,
        )