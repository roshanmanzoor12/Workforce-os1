from __future__ import annotations

import uuid

import pytest

from app.modules.attachments.limits import (
    MIB,
    get_attachment_limit_bytes,
    validate_attachment_size,
)
from app.modules.attachments.models import (
    AttachmentKind,
    AttachmentScope,
    AttachmentStatus,
)
from app.modules.attachments.service import (
    classify_attachment_kind,
    sanitize_filename,
)


def test_free_limit_is_10_mb() -> None:
    assert (
        get_attachment_limit_bytes("FREE")
        == 10 * MIB
    )


def test_starter_limit_is_50_mb() -> None:
    assert (
        get_attachment_limit_bytes("STARTER")
        == 50 * MIB
    )


def test_professional_limit_is_250_mb() -> None:
    assert (
        get_attachment_limit_bytes(
            "PROFESSIONAL"
        )
        == 250 * MIB
    )


def test_business_limit_is_1_gb() -> None:
    assert (
        get_attachment_limit_bytes("BUSINESS")
        == 1024 * MIB
    )


def test_unknown_plan_falls_back_to_free() -> None:
    assert (
        get_attachment_limit_bytes(
            "UNKNOWN"
        )
        == 10 * MIB
    )


def test_missing_plan_falls_back_to_free() -> None:
    assert (
        get_attachment_limit_bytes(None)
        == 10 * MIB
    )


def test_free_exact_limit_allowed() -> None:
    limit = validate_attachment_size(
        plan_code="FREE",
        size_bytes=10 * MIB,
    )

    assert limit == 10 * MIB


def test_free_over_limit_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="10 MB",
    ):
        validate_attachment_size(
            plan_code="FREE",
            size_bytes=(10 * MIB) + 1,
        )


def test_zero_size_rejected() -> None:
    with pytest.raises(ValueError):
        validate_attachment_size(
            plan_code="FREE",
            size_bytes=0,
        )


@pytest.mark.parametrize(
    ("content_type", "expected"),
    [
        (
            "image/png",
            AttachmentKind.IMAGE,
        ),
        (
            "image/jpeg",
            AttachmentKind.IMAGE,
        ),
        (
            "video/mp4",
            AttachmentKind.VIDEO,
        ),
        (
            "audio/mpeg",
            AttachmentKind.AUDIO,
        ),
        (
            "application/pdf",
            AttachmentKind.FILE,
        ),
        (
            "application/zip",
            AttachmentKind.FILE,
        ),
    ],
)
def test_attachment_kind_detection(
    content_type: str,
    expected: AttachmentKind,
) -> None:
    assert (
        classify_attachment_kind(
            content_type
        )
        == expected
    )


def test_filename_is_sanitized() -> None:
    result = sanitize_filename(
        "../../weird file !@#.png"
    )

    assert "/" not in result
    assert "\\" not in result
    assert " " not in result
    assert result.endswith(".png")


def test_attachment_scope_values() -> None:
    assert (
        AttachmentScope.CONVERSATION.value
        == "CONVERSATION"
    )

    assert (
        AttachmentScope.CHANNEL.value
        == "CHANNEL"
    )


def test_attachment_status_values() -> None:
    assert AttachmentStatus.PENDING.value == "PENDING"
    assert AttachmentStatus.READY.value == "READY"
    assert AttachmentStatus.DELETED.value == "DELETED"
    assert AttachmentStatus.FAILED.value == "FAILED"


def test_uuid_object_key_components_are_safe() -> None:
    user_id = uuid.uuid4()
    attachment_id = uuid.uuid4()

    key = (
        f"conversation/"
        f"{user_id}/"
        f"{attachment_id}/"
        f"example.png"
    )

    assert ".." not in key
    assert key.startswith("conversation/")