from __future__ import annotations

import ast
from pathlib import Path


BACKEND_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

ATTACHMENT_SERVICE = (
    BACKEND_ROOT
    / "app"
    / "modules"
    / "attachments"
    / "service.py"
)


def main() -> None:
    source = ATTACHMENT_SERVICE.read_text(
        encoding="utf-8",
        errors="strict",
    )

    tree = ast.parse(
        source,
        filename=str(
            ATTACHMENT_SERVICE
        ),
    )

    bad_lines: list[int] = []

    left_at_found = False
    channel_active_found = False

    for node in ast.walk(
        tree
    ):
        if not isinstance(
            node,
            ast.Attribute,
        ):
            continue

        if (
            node.attr
            == "is_active"
            and isinstance(
                node.value,
                ast.Name,
            )
            and node.value.id
            == "WorkspaceChannelMember"
        ):
            bad_lines.append(
                node.lineno
            )

        if (
            node.attr == "left_at"
            and isinstance(
                node.value,
                ast.Name,
            )
            and node.value.id
            == "WorkspaceChannelMember"
        ):
            left_at_found = True

        if (
            node.attr == "is_active"
            and isinstance(
                node.value,
                ast.Name,
            )
            and node.value.id
            == "WorkspaceChannel"
        ):
            channel_active_found = True

    if bad_lines:
        raise SystemExit(
            "FAIL: attachment service "
            "references "
            "WorkspaceChannelMember.is_active "
            f"at lines {bad_lines}"
        )

    if not left_at_found:
        raise SystemExit(
            "FAIL: attachment service "
            "does not enforce "
            "WorkspaceChannelMember.left_at."
        )

    if not channel_active_found:
        raise SystemExit(
            "FAIL: attachment service "
            "does not verify active channel."
        )

    print(
        "PASS attachment channel "
        "membership lifecycle"
    )


if __name__ == "__main__":
    main()