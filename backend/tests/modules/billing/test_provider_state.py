import pytest

from app.modules.billing.provider_state import (
    normalize_provider_subscription_id,
)


def test_subscription_id_is_trimmed():
    result = (
        normalize_provider_subscription_id(
            "  sub_123  "
        )
    )

    assert result == "sub_123"


def test_empty_subscription_id_rejected():
    with pytest.raises(
        ValueError,
        match="required",
    ):
        normalize_provider_subscription_id(
            "   "
        )


def test_long_subscription_id_rejected():
    with pytest.raises(
        ValueError,
        match="too long",
    ):
        normalize_provider_subscription_id(
            "x" * 256
        )