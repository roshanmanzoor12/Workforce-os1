from fastapi.routing import APIRoute

from app.modules.chat.router import (
    router as chat_router,
)
from app.modules.friends.router import (
    router as friends_router,
)


def get_contract(
    router,
) -> set[
    tuple[str, str]
]:
    result: set[
        tuple[str, str]
    ] = set()

    for route in router.routes:
        if not isinstance(
            route,
            APIRoute,
        ):
            continue

        for method in route.methods:
            result.add(
                (
                    method,
                    route.path,
                )
            )

    return result


def test_friends_router_contract():
    contract = get_contract(
        friends_router
    )

    expected = {
        (
            "POST",
            "/friends/requests/{target_user_id}",
        ),
        (
            "POST",
            "/friends/requests/{friendship_id}/accept",
        ),
        (
            "DELETE",
            "/friends/requests/{friendship_id}",
        ),
        (
            "POST",
            "/friends/blocks/{target_user_id}",
        ),
        (
            "DELETE",
            "/friends/blocks/{target_user_id}",
        ),
        (
            "GET",
            "/friends",
        ),
    }

    assert expected.issubset(
        contract
    )


def test_chat_router_contract():
    contract = get_contract(
        chat_router
    )

    expected = {
        (
            "POST",
            "/chat/direct",
        ),
        (
            "POST",
            "/chat/groups",
        ),
        (
            "GET",
            "/chat/conversations",
        ),
        (
            "POST",
            "/chat/{conversation_id}/members/{target_user_id}",
        ),
        (
            "DELETE",
            "/chat/{conversation_id}/members/{target_user_id}",
        ),
        (
            "POST",
            "/chat/{conversation_id}/messages",
        ),
        (
            "GET",
            "/chat/{conversation_id}/messages",
        ),
        (
            "PATCH",
            "/chat/{conversation_id}/messages/{message_id}",
        ),
        (
            "DELETE",
            "/chat/{conversation_id}/messages/{message_id}",
        ),
        (
            "POST",
            "/chat/{conversation_id}/read/{message_id}",
        ),
        (
            "GET",
            "/chat/{conversation_id}/read-receipts/{message_id}",
        ),
        (
            "PUT",
            "/chat/presence",
        ),
        (
            "GET",
            "/chat/presence/{target_user_id}",
        ),
    }

    assert expected.issubset(
        contract
    )


def test_friends_route_count():
    routes = [
        route
        for route in friends_router.routes
        if isinstance(
            route,
            APIRoute,
        )
    ]

    assert len(routes) == 6


def test_chat_route_count():
    routes = [
        route
        for route in chat_router.routes
        if isinstance(
            route,
            APIRoute,
        )
    ]

    assert len(routes) == 13