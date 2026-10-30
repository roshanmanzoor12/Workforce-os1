from __future__ import annotations

from collections.abc import Mapping


CHANNEL_BASE = "/workspace-channels"

REALTIME_BASE = (
    "/workspaces/{workspace_id}"
    "/channels/{channel_id}/realtime"
)


CHANNEL_ROUTES = {
    "create_channel": (
        CHANNEL_BASE,
        "post",
    ),

    "list_channels": (
        f"{CHANNEL_BASE}/workspace/"
        "{workspace_id}",
        "get",
    ),

    "rename_channel": (
        f"{CHANNEL_BASE}/"
        "{channel_id}",
        "patch",
    ),

    "archive_channel": (
        f"{CHANNEL_BASE}/"
        "{channel_id}",
        "delete",
    ),

    "create_message": (
        f"{CHANNEL_BASE}/"
        "{channel_id}/messages",
        "post",
    ),

    "list_messages": (
        f"{CHANNEL_BASE}/"
        "{channel_id}/messages",
        "get",
    ),

    "update_message": (
        f"{CHANNEL_BASE}/"
        "{channel_id}/messages/"
        "{message_id}",
        "patch",
    ),

    "delete_message": (
        f"{CHANNEL_BASE}/"
        "{channel_id}/messages/"
        "{message_id}",
        "delete",
    ),

    "workspace_read_state": (
        f"{CHANNEL_BASE}/workspace/"
        "{workspace_id}/read-state",
        "get",
    ),

    "channel_read_state": (
        f"{CHANNEL_BASE}/"
        "{channel_id}/read-state",
        "get",
    ),

    "mark_message_read": (
        f"{CHANNEL_BASE}/"
        "{channel_id}/read/"
        "{message_id}",
        "post",
    ),

    "mark_all_read": (
        f"{CHANNEL_BASE}/"
        "{channel_id}/read-all",
        "post",
    ),

    "bind_attachments": (
        f"{CHANNEL_BASE}/"
        "{channel_id}/messages/"
        "{message_id}/attachments",
        "post",
    ),

    "list_attachments": (
        f"{CHANNEL_BASE}/"
        "{channel_id}/messages/"
        "{message_id}/attachments",
        "get",
    ),
}


REALTIME_ROUTES = {
    "ticket": (
        f"{REALTIME_BASE}/ticket",
        "post",
    ),

    "resume": (
        f"{REALTIME_BASE}/resume",
        "post",
    ),

    "typing_start": (
        f"{REALTIME_BASE}/typing/start",
        "post",
    ),

    "typing_stop": (
        f"{REALTIME_BASE}/typing/stop",
        "post",
    ),

    "heartbeat": (
        f"{REALTIME_BASE}/heartbeat",
        "post",
    ),

    "capabilities": (
        f"{REALTIME_BASE}/capabilities",
        "get",
    ),
}


def find_path(
    paths: Mapping[str, object],
    expected_suffix: str,
) -> str | None:
    if expected_suffix in paths:
        return expected_suffix

    for path in paths:
        if path.endswith(
            expected_suffix
        ):
            return path

    return None


def require_path(
    paths: Mapping[str, object],
    expected_suffix: str,
) -> str:
    resolved = find_path(
        paths,
        expected_suffix,
    )

    assert resolved is not None, (
        "Missing Phase 21 route: "
        f"{expected_suffix}"
    )

    return resolved


__all__ = [
    "CHANNEL_BASE",
    "REALTIME_BASE",
    "CHANNEL_ROUTES",
    "REALTIME_ROUTES",
    "find_path",
    "require_path",
]