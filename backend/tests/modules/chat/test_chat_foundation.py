from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from app.modules.chat.enums import (
    ConversationMemberRole,
    ConversationType,
    MessageType,
)
from app.modules.chat.schemas import (
    GroupConversationCreateRequest,
    MessageCreateRequest,
)


def test_conversation_types():
    assert (
        ConversationType.DIRECT.value
        == "direct"
    )

    assert (
        ConversationType.GROUP.value
        == "group"
    )


def test_member_roles():
    assert (
        ConversationMemberRole.OWNER.value
        == "owner"
    )

    assert (
        ConversationMemberRole.ADMIN.value
        == "admin"
    )

    assert (
        ConversationMemberRole.MEMBER.value
        == "member"
    )


def test_message_type_text():
    assert (
        MessageType.TEXT.value
        == "text"
    )


def test_group_name_is_trimmed():
    request = (
        GroupConversationCreateRequest(
            name="  Workforce Friends  ",
            member_user_ids=[
                uuid.uuid4(),
            ],
        )
    )

    assert (
        request.name
        == "Workforce Friends"
    )


def test_blank_group_name_rejected():
    with pytest.raises(
        ValidationError
    ):
        GroupConversationCreateRequest(
            name="   ",
            member_user_ids=[
                uuid.uuid4(),
            ],
        )


def test_message_content_trimmed():
    request = MessageCreateRequest(
        content="   hello world   "
    )

    assert (
        request.content
        == "hello world"
    )


def test_blank_message_rejected():
    with pytest.raises(
        ValidationError
    ):
        MessageCreateRequest(
            content="    "
        )