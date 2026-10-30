from __future__ import annotations

from collections.abc import Mapping


REPORT_CATALOG = (
    "attendance",
    "payroll",
    "productivity",
    "device_health",
    "monitoring_summary",
    "goals",
    "audit",
)


REPORT_PERMISSION_NAMES = (
    "reports.self.read",
    "reports.team.read",
    "reports.all.read",
    "reports.export",
)


SOURCE_ROUTE_MARKERS = {
    "attendance": (
        "/attendance/",
        "/attendance",
    ),

    "payroll": (
        "/payroll",
        "/compensation",
    ),

    "productivity": (
        "/productivity",
        "/productivity-insights",
        "/analytics/productivity",
    ),

    "device_health": (
        "/devices",
    ),

    "monitoring_summary": (
        "/monitoring",
        "/live-monitoring",
    ),

    "goals": (
        "/goals",
    ),

    "audit": (
        "/audit-log",
    ),
}


def find_matching_get_paths(
    paths: Mapping[str, object],
    markers: tuple[str, ...],
) -> list[str]:
    matches: list[str] = []

    for path, operations in paths.items():
        if not isinstance(
            operations,
            Mapping,
        ):
            continue

        if (
            "get"
            not in operations
        ):
            continue

        if any(
            marker in path
            for marker in markers
        ):
            matches.append(
                path
            )

    return sorted(
        matches
    )


def find_report_paths(
    paths: Mapping[str, object],
) -> list[str]:
    return sorted(
        path
        for path
        in paths
        if (
            "/reports"
            in path
            or "/report-"
            in path
        )
    )


__all__ = [
    "REPORT_CATALOG",
    "REPORT_PERMISSION_NAMES",
    "SOURCE_ROUTE_MARKERS",
    "find_matching_get_paths",
    "find_report_paths",
]