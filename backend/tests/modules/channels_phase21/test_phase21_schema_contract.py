from __future__ import annotations

import pytest

from pydantic import (
    ValidationError,
)

from app.modules.channels.enums import (
    WorkspaceChannelMessageType,
    WorkspaceChannelType,
)
from app.modules.channels.schemas import (
    WorkspaceChannelCreateRequest,
    WorkspaceChannelMessageCreateRequest,
    WorkspaceChannelMessagePublic,
    WorkspaceChannelPublic,
    make_channel_slug,
)


def test_channel_type_supports_text():
    values = {
        item.value
        for item
        in WorkspaceChannelType
    }

    assert "text" in values


def test_channel_type_supports_announcement():
    values = {
        item.value
        for item
        in WorkspaceChannelType
    }

    assert (
        "announcement"
        in values
    ), (
        "Phase 21 requires an "
        "announcement channel type."
    )


def test_message_type_supports_text():
    values = {
        item.value
        for item
        in WorkspaceChannelMessageType
    }

    assert "text" in values


def test_channel_slug_contract():
    assert (
        make_channel_slug(
            " Product & Design "
        )
        == "product-design"
    )


def test_empty_message_rejected():
    with pytest.raises(
        ValidationError
    ):
        (
            WorkspaceChannelMessageCreateRequest(
                content="   "
            )
        )


def test_message_length_is_bounded():
    with pytest.raises(
        ValidationError
    ):
        (
            WorkspaceChannelMessageCreateRequest(
                content=(
                    "x"
                    * 10001
                )
            )
        )


def test_public_channel_has_workspace_identity():
    fields = set(
        WorkspaceChannelPublic
        .model_fields
    )

    assert {
        "id",
        "workspace_id",
        "channel_type",
        "is_active",
    }.issubset(
        fields
    )


def test_public_message_has_mutation_state():
    fields = set(
        WorkspaceChannelMessagePublic
        .model_fields
    )

    assert {
        "id",
        "channel_id",
        "sender_user_id",
        "edited_at",
        "deleted_at",
        "created_at",
    }.issubset(
        fields
    )