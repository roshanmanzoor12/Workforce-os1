from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from app.main import app


ROOT = Path(
    r"C:\workforce-os\backend"
)


REPORT_FILES = (
    ROOT
    / "app"
    / "modules"
    / "reports"
)


MODULE_CANDIDATES = [
    "app.modules.reports",
    "app.modules.analytics",
    "app.modules.payroll",
    "app.modules.devices",
    "app.modules.goals",
    "app.modules.audit_log",
    "app.modules.monitoring",
    "app.modules.monitoring_admin",
    "app.modules.monitoring_control",
    "app.modules.live_monitoring",
]


def module_exists(
    module_name: str,
) -> bool:
    return (
        importlib.util.find_spec(
            module_name
        )
        is not None
    )


def main() -> None:
    schema = app.openapi()

    paths = sorted(
        schema.get(
            "paths",
            {},
        )
    )

    report_paths = [
        path
        for path
        in paths
        if (
            "/reports"
            in path
            or "/report-"
            in path
        )
    ]

    source_paths = {
        "attendance": [
            path
            for path
            in paths
            if "/attendance" in path
        ],

        "payroll": [
            path
            for path
            in paths
            if (
                "/payroll"
                in path
                or "/compensation"
                in path
            )
        ],

        "productivity": [
            path
            for path
            in paths
            if "/productivity" in path
        ],

        "devices": [
            path
            for path
            in paths
            if "/devices" in path
        ],

        "monitoring": [
            path
            for path
            in paths
            if "monitoring" in path
        ],

        "goals": [
            path
            for path
            in paths
            if "/goals" in path
        ],

        "audit": [
            path
            for path
            in paths
            if "/audit-log" in path
        ],
    }

    report_files: list[str] = []

    if REPORT_FILES.exists():
        report_files = sorted(
            str(
                path.relative_to(
                    ROOT
                )
            )
            for path
            in REPORT_FILES.rglob(
                "*.py"
            )
        )

    result = {
        "dedicated_reports_module": (
            REPORT_FILES.exists()
        ),

        "report_module_files": (
            report_files
        ),

        "module_candidates": {
            module_name: (
                module_exists(
                    module_name
                )
            )
            for module_name
            in MODULE_CANDIDATES
        },

        "dedicated_report_paths": (
            report_paths
        ),

        "source_paths": (
            source_paths
        ),

        "openapi_path_count": (
            len(
                paths
            )
        ),
    }

    print(
        json.dumps(
            result,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()