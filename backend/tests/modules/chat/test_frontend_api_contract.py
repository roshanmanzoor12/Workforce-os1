from __future__ import annotations

from app.main import app


def test_frontend_chat_api_contract():
    paths = app.openapi().get(
        "paths",
        {},
    )

    required = {
        "/api/v1/chat/direct": {
            "post",
        },
        "/api/v1/chat/groups": {
            "post",
        },
        "/api/v1/chat/conversations": {
            "get",
        },
        "/api/v1/chat/{conversation_id}/messages": {
            "get",
            "post",
        },
        "/api/v1/chat/{conversation_id}/messages-page": {
            "get",
        },
        "/api/v1/chat/realtime/ticket": {
            "post",
        },
        "/api/v1/chat/realtime/heartbeat": {
            "post",
        },
        "/api/v1/chat/realtime/resume": {
            "post",
        },
    }

    for path, methods in required.items():
        assert path in paths

        for method in methods:
            assert (
                method
                in paths[path]
            )


def test_frontend_friends_api_contract():
    paths = app.openapi().get(
        "paths",
        {},
    )

    required = {
        "/api/v1/friends": {
            "get",
        },
        "/api/v1/friends/requests/{target_user_id}": {
            "post",
        },
        "/api/v1/friends/requests/{friendship_id}/accept": {
            "post",
        },
    }

    for path, methods in required.items():
        assert path in paths

        for method in methods:
            assert (
                method
                in paths[path]
            )


def test_frontend_workspace_channel_contract():
    paths = app.openapi().get(
        "paths",
        {},
    )

    required = {
        "/api/v1/workspace-channels": {
            "post",
        },
        "/api/v1/workspace-channels/workspace/{workspace_id}": {
            "get",
        },
        "/api/v1/workspace-channels/{channel_id}/messages": {
            "get",
            "post",
        },
    }

    for path, methods in required.items():
        assert path in paths

        for method in methods:
            assert (
                method
                in paths[path]
            )