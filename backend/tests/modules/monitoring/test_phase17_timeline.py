from __future__ import annotations

import inspect

from app.modules.timeline.enums import (
    TimelineEntityType,
    TimelineEventType,
    TimelineSourceKey,
)
from app.modules.timeline.registry import (
    TimelineSourceRegistry,
)
from app.modules.timeline.sources import (
    ScreenshotTimelineSource,
)


def test_screenshot_timeline_enums_exist():
    assert (
        TimelineSourceKey.SCREENSHOTS
        .value
        == "screenshots"
    )

    assert (
        TimelineEntityType
        .SCREENSHOT_CAPTURE
        .value
        == "screenshot_capture"
    )

    expected = {
        "screenshot.requested",
        "screenshot.completed",
        "screenshot.denied",
        "screenshot.expired",
        "screenshot.failed",
    }

    actual = {
        TimelineEventType
        .SCREENSHOT_REQUESTED
        .value,

        TimelineEventType
        .SCREENSHOT_COMPLETED
        .value,

        TimelineEventType
        .SCREENSHOT_DENIED
        .value,

        TimelineEventType
        .SCREENSHOT_EXPIRED
        .value,

        TimelineEventType
        .SCREENSHOT_FAILED
        .value,
    }

    assert actual == expected


def test_screenshot_timeline_source_is_privacy_safe():
    source = inspect.getsource(
        ScreenshotTimelineSource
        .list_events
    )

    assert (
        "storage_object_key"
        not in source
    )

    assert "sha256" not in source

    assert (
        "device_id"
        in source
    )

    assert "status" in source


def test_registry_includes_screenshot_source():
    source = inspect.getsource(
        TimelineSourceRegistry
        .__init__
    )

    assert (
        "SCREENSHOTS"
        in source
    )

    assert (
        "ScreenshotTimelineSource"
        in source
    )