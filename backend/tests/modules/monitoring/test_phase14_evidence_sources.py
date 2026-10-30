from __future__ import annotations

import inspect

from app.modules.activity.repository import (
    ActivityRepository,
)
from app.modules.app_tracking.query_service import (
    AppTrackingQueryService,
)
from app.modules.work_sessions.repository import (
    WorkSessionRepository,
)


def test_activity_repository_has_current_employee_evidence():
    assert callable(
        getattr(
            ActivityRepository,
            "get_latest_for_employee",
            None,
        )
    )


def test_activity_repository_has_history():
    assert callable(
        getattr(
            ActivityRepository,
            "list_for_employee",
            None,
        )
    )


def test_app_tracking_has_current_observation():
    assert callable(
        getattr(
            AppTrackingQueryService,
            "get_latest_observation",
            None,
        )
    )


def test_app_tracking_has_current_interval():
    assert callable(
        getattr(
            AppTrackingQueryService,
            "get_current_interval",
            None,
        )
    )


def test_work_sessions_support_current_open_session():
    assert callable(
        getattr(
            WorkSessionRepository,
            "get_open_for_device",
            None,
        )
    )


def test_work_sessions_support_employee_history():
    assert callable(
        getattr(
            WorkSessionRepository,
            "list_for_employee",
            None,
        )
    )


def test_monitoring_sources_are_persisted_queries():
    activity_source = inspect.getsource(
        ActivityRepository
    )

    app_source = inspect.getsource(
        AppTrackingQueryService
    )

    session_source = inspect.getsource(
        WorkSessionRepository
    )

    for source in (
        activity_source,
        app_source,
        session_source,
    ):
        assert (
            "select("
            in source
        )