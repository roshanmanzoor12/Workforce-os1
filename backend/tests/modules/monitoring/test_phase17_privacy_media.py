from __future__ import annotations

import inspect

from app.modules.live_monitoring.phase17 import (
    create_screenshot_download_url,
    record_screenshot_audit,
)
from app.modules.live_monitoring.schemas import (
    ScreenshotMediaResponse,
    ScreenshotResponse,
)


def test_browser_history_does_not_expose_object_key():
    fields = {
        name.lower()
        for name
        in ScreenshotResponse
        .model_fields
        .keys()
    }

    assert (
        "storage_object_key"
        not in fields
    )


def test_browser_history_does_not_expose_raw_hash():
    fields = {
        name.lower()
        for name
        in ScreenshotResponse
        .model_fields
        .keys()
    }

    assert "sha256" not in fields


def test_media_response_only_contains_safe_contract():
    fields = set(
        ScreenshotMediaResponse
        .model_fields
        .keys()
    )

    assert fields == {
        "request_id",
        "download_url",
        "expires_in_seconds",
    }


def test_media_uses_private_presigned_storage():
    source = inspect.getsource(
        create_screenshot_download_url
    )

    assert (
        "create_download_url"
        in source
    )

    assert (
        "SCREENSHOT_MEDIA_URL_SECONDS"
        in source
    )


def test_sensitive_access_is_audited():
    source = inspect.getsource(
        record_screenshot_audit
    )

    assert (
        "AuditLogService"
        in source
    )

    assert (
        'category="monitoring"'
        in source
    )

    assert (
        "target_type="
        in source
    )