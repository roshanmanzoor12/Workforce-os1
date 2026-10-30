from __future__ import annotations

import ast
from pathlib import Path


BACKEND_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)


def read_source(
    relative: str,
) -> str:
    return (
        BACKEND_ROOT
        / relative
    ).read_text(
        encoding="utf-8",
    )


def test_channel_access_uses_left_at() -> None:
    source = read_source(
        "app/modules/channels/"
        "hardening/access.py"
    )

    assert (
        "WorkspaceChannelMember.left_at"
        in source
    )


def test_channel_access_rejects_inactive_channel() -> None:
    source = read_source(
        "app/modules/channels/"
        "hardening/access.py"
    )

    assert (
        "WorkspaceChannel.is_active"
        in source
    )


def test_attachment_access_has_no_member_is_active() -> None:
    path = (
        BACKEND_ROOT
        / "app"
        / "modules"
        / "attachments"
        / "service.py"
    )

    source = path.read_text(
        encoding="utf-8",
    )

    tree = ast.parse(
        source,
        filename=str(path),
    )

    bad = []

    for node in ast.walk(
        tree
    ):
        if not isinstance(
            node,
            ast.Attribute,
        ):
            continue

        if (
            node.attr == "is_active"
            and isinstance(
                node.value,
                ast.Name,
            )
            and node.value.id
            == "WorkspaceChannelMember"
        ):
            bad.append(
                node.lineno
            )

    assert bad == []


def test_attachment_access_uses_left_at() -> None:
    source = read_source(
        "app/modules/attachments/"
        "service.py"
    )

    assert (
        "WorkspaceChannelMember.left_at"
        in source
    )


def test_read_state_repository_uses_upserter() -> None:
    source = read_source(
        "app/modules/channels/"
        "read_state_repository.py"
    )

    assert (
        "ChannelReadStateUpserter"
        in source
    )

    assert (
        ".upsert_and_flush("
        in source
    )


def test_read_state_upserter_uses_on_conflict() -> None:
    source = read_source(
        "app/modules/channels/"
        "hardening/read_state_upsert.py"
    )

    assert (
        ".on_conflict_do_update("
        in source
    )