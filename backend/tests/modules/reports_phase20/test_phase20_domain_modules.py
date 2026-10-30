from __future__ import annotations

import importlib.util


REQUIRED_SOURCE_MODULES = {
    "analytics": (
        "app.modules.analytics"
    ),

    "payroll": (
        "app.modules.payroll"
    ),

    "devices": (
        "app.modules.devices"
    ),

    "goals": (
        "app.modules.goals"
    ),

    "audit": (
        "app.modules.audit_log"
    ),
}


MONITORING_CANDIDATES = (
    "app.modules.monitoring",
    "app.modules.monitoring_admin",
    "app.modules.monitoring_control",
    "app.modules.live_monitoring",
)


def module_exists(
    module_name: str,
) -> bool:
    return (
        importlib.util.find_spec(
            module_name
        )
        is not None
    )


def test_required_report_source_modules_exist():
    missing: list[str] = []

    for (
        source_name,
        module_name,
    ) in REQUIRED_SOURCE_MODULES.items():
        if not module_exists(
            module_name
        ):
            missing.append(
                (
                    f"{source_name}:"
                    f"{module_name}"
                )
            )

    assert not missing, (
        "Missing report source modules: "
        f"{missing}"
    )


def test_monitoring_report_source_exists():
    assert any(
        module_exists(
            candidate
        )
        for candidate
        in MONITORING_CANDIDATES
    ), (
        "No monitoring source module "
        "was found for reports."
    )