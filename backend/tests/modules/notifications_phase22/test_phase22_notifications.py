from __future__ import annotations

from app.main import app


EXPECTED_ROUTES = {
    ("GET", "/api/v1/notifications"),
    ("GET", "/api/v1/notifications/unread-count"),
    (
        "POST",
        "/api/v1/notifications/{notification_id}/read",
    ),
    ("POST", "/api/v1/notifications/read-all"),
    (
        "DELETE",
        "/api/v1/notifications/{notification_id}",
    ),
}


def test_notification_routes_exist():
    routes = {
        (
            method.upper(),
            route.path,
        )
        for route in app.routes
        for method in (
            getattr(route, "methods", None)
            or set()
        )
        if getattr(route, "path", None)
    }

    missing = EXPECTED_ROUTES - routes

    assert not missing, (
        "Missing Phase 22 notification routes: "
        f"{sorted(missing)!r}"
    )


def test_notification_routes_use_api_v1_prefix():
    paths = {
        route.path
        for route in app.routes
        if getattr(route, "path", None)
    }

    notification_paths = {
        path
        for path in paths
        if "/notifications" in path
    }

    assert notification_paths
    assert all(
        path.startswith("/api/v1/")
        for path in notification_paths
    )


def test_notification_module_contract_exists():
    from app.modules.notifications.router import router
    from app.modules.notifications.repository import (
        NotificationRepository,
    )
    from app.modules.notifications.service import (
        NotificationService,
    )

    assert router is not None
    assert NotificationRepository is not None
    assert NotificationService is not None


def test_notification_service_surface_exists():
    from app.modules.notifications.service import (
        NotificationService,
    )

    required_methods = {
        "list_notifications",
        "unread_count",
        "mark_read",
        "mark_all_read",
        "delete_notification",
        "create_notification",
    }

    missing = {
        method
        for method in required_methods
        if not hasattr(NotificationService, method)
    }

    assert not missing, (
        "NotificationService is missing methods: "
        f"{sorted(missing)!r}"
    )


def test_notification_repository_surface_exists():
    from app.modules.notifications.repository import (
        NotificationRepository,
    )

    required_methods = {
        "list_for_user",
        "count_unread",
        "get_for_user",
        "mark_read",
        "mark_all_read",
        "delete_for_user",
        "create",
    }

    missing = {
        method
        for method in required_methods
        if not hasattr(NotificationRepository, method)
    }

    assert not missing, (
        "NotificationRepository is missing methods: "
        f"{sorted(missing)!r}"
    )