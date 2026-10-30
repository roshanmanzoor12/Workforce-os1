from __future__ import annotations

import inspect

from app.modules.app_tracking.repository import (
    AppTrackingRepository,
)
from app.modules.employee_monitoring_detail.schemas import (
    EmployeeMonitoringDetailResponse,
)
from app.modules.employee_monitoring_detail.service import (
    EmployeeMonitoringDetailService,
)
from app.modules.website_tracking.repository import (
    WebsiteTrackingRepository,
)


FORBIDDEN_RESPONSE_FIELDS = {
    "device_secret",
    "secret_hash",
    "credential_hash",
    "last_ip_address",
    "storage_object_key",
    "sha256",
    "executable_path",
    "window_title",
    "page_url",
    "page_title",
    "keystrokes",
    "typed_text",
    "clipboard",
    "password",
}


def _all_schema_property_names(
    schema,
) -> set[str]:
    result: set[str] = set()

    if isinstance(
        schema,
        dict,
    ):
        properties = schema.get(
            "properties",
            {},
        )

        if isinstance(
            properties,
            dict,
        ):
            result.update(
                str(key).lower()
                for key
                in properties.keys()
            )

        for value in schema.values():
            result.update(
                _all_schema_property_names(
                    value
                )
            )

    elif isinstance(
        schema,
        list,
    ):
        for value in schema:
            result.update(
                _all_schema_property_names(
                    value
                )
            )

    return result


def test_employee_monitoring_response_is_browser_safe():
    schema = (
        EmployeeMonitoringDetailResponse
        .model_json_schema()
    )

    fields = (
        _all_schema_property_names(
            schema
        )
    )

    leaked = sorted(
        fields
        & FORBIDDEN_RESPONSE_FIELDS
    )

    assert not leaked, (
        "Employee Monitoring Detail "
        "exposes forbidden fields: "
        + ", ".join(
            leaked
        )
    )


def test_employee_app_repository_supports_employee_history():
    assert callable(
        getattr(
            AppTrackingRepository,
            "list_intervals_for_employee",
            None,
        )
    )


def test_employee_website_repository_supports_employee_history():
    assert callable(
        getattr(
            WebsiteTrackingRepository,
            "list_employee_intervals",
            None,
        )
    )


def test_employee_monitoring_service_does_not_call_agent_routes():
    source = inspect.getsource(
        EmployeeMonitoringDetailService
    )

    assert (
        "/device-agent/"
        not in source
    )


def test_employee_monitoring_service_uses_persisted_employee_sources():
    source = inspect.getsource(
        EmployeeMonitoringDetailService
    )

    expected = (
        "get_latest_for_employee",
        "list_intervals_for_employee",
        "list_employee_intervals",
        "list_for_employee",
        "list_screenshots",
    )

    missing = [
        item
        for item in expected
        if item not in source
    ]

    assert not missing, (
        "Employee detail is missing "
        "persisted evidence sources: "
        + ", ".join(
            missing
        )
    )