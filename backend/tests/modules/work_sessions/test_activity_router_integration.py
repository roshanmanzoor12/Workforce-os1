from __future__ import annotations

from pathlib import Path


def activity_router_path() -> Path:
    backend_root = (
        Path(__file__)
        .resolve()
        .parents[3]
    )

    return (
        backend_root
        / "app"
        / "modules"
        / "activity"
        / "agent_router.py"
    )


def test_activity_router_contains_work_session_live_hook() -> None:
    path = activity_router_path()

    assert path.exists()

    source = path.read_text(
        encoding="utf-8"
    )

    assert (
        "process_persisted_activity_event"
        in source
    )

    assert (
        "response.event_id"
        in source
    )


def test_activity_state_route_still_exists() -> None:
    source = activity_router_path().read_text(
        encoding="utf-8"
    )

    assert (
        '"/activity-state"'
        in source
    )

    assert (
        "ActivityStateResponse"
        in source
    )


def test_activity_status_route_still_exists() -> None:
    source = activity_router_path().read_text(
        encoding="utf-8"
    )

    assert (
        '"/activity-status"'
        in source
    )

    assert (
        "ActivityStatusResponse"
        in source
    )