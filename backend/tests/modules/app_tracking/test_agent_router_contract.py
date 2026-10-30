from __future__ import annotations

from pathlib import Path


def router_path() -> Path:
    backend_root = (
        Path(__file__)
        .resolve()
        .parents[3]
    )

    return (
        backend_root
        / "app"
        / "modules"
        / "app_tracking"
        / "agent_router.py"
    )


def test_app_observation_route_exists() -> None:
    source = router_path().read_text(
        encoding="utf-8"
    )

    assert (
        '"/app-observation"'
        in source
    )

    assert (
        "AppObservationResponse"
        in source
    )


def test_route_uses_authenticated_device_dependency() -> None:
    source = router_path().read_text(
        encoding="utf-8"
    )

    assert (
        "get_authenticated_device"
        in source
    )

    assert (
        "authenticated_device.database_name"
        in source
    )


def test_agent_cannot_supply_employee_assignment() -> None:
    source = router_path().read_text(
        encoding="utf-8"
    )

    assert (
        "employee_id=None"
        in source
    )


def test_window_title_capture_is_disabled_in_agent_ingestion() -> None:
    source = router_path().read_text(
        encoding="utf-8"
    )

    assert (
        "capture_window_titles=False"
        in source
    )