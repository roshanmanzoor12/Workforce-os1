from __future__ import annotations

from datetime import (
    datetime,
    timedelta,
    timezone,
)
from types import (
    SimpleNamespace,
)
import uuid

import pytest

from app.modules.live_monitoring.screenshot_retention import (
    ScreenshotRetentionService,
    retention_cutoff,
)


NOW = datetime(
    2026,
    9,
    30,
    tzinfo=timezone.utc,
)


class FakeScalars:
    def __init__(
        self,
        items,
    ) -> None:
        self.items = items

    def all(
        self,
    ):
        return list(
            self.items
        )


class FakeResult:
    def __init__(
        self,
        items,
    ) -> None:
        self.items = items

    def scalars(
        self,
    ) -> FakeScalars:
        return FakeScalars(
            self.items
        )


class FakeSession:
    def __init__(
        self,
        items,
    ) -> None:
        self.items = items

        self.deleted = []

        self.flush_count = 0

        self.commit_count = 0

        self.rollback_count = 0

    async def execute(
        self,
        statement,
    ):
        del statement

        return FakeResult(
            self.items
        )

    async def delete(
        self,
        item,
    ) -> None:
        self.deleted.append(
            item
        )

    async def flush(
        self,
    ) -> None:
        self.flush_count += 1

    async def commit(
        self,
    ) -> None:
        self.commit_count += 1

    async def rollback(
        self,
    ) -> None:
        self.rollback_count += 1


def _item(
    *,
    object_key: str | None,
):
    return SimpleNamespace(
        id=uuid.uuid4(),

        storage_object_key=(
            object_key
        ),
    )


def test_retention_cutoff():
    cutoff = retention_cutoff(
        retention_days=30,
        now=NOW,
    )

    assert cutoff == (
        NOW
        - timedelta(
            days=30
        )
    )


@pytest.mark.asyncio
async def test_cleanup_deletes_database_record_without_media(
    monkeypatch,
):
    item = _item(
        object_key=None
    )

    session = FakeSession(
        [
            item,
        ]
    )

    service = (
        ScreenshotRetentionService(
            session
        )
    )

    result = await service.cleanup(
        retention_days=30,
        now=NOW,
        limit=500,
    )

    assert session.deleted == [
        item,
    ]

    assert result.deleted == 1

    assert (
        result.storage_failures
        == 0
    )

    assert (
        result.database_failures
        == 0
    )


@pytest.mark.asyncio
async def test_cleanup_deletes_storage_before_database(
    monkeypatch,
):
    item = _item(
        object_key=(
            "screenshots/example.png"
        )
    )

    deleted_objects = []

    def fake_delete_object(
        *,
        object_key: str,
    ) -> None:
        deleted_objects.append(
            object_key
        )

    monkeypatch.setattr(
        (
            "app.modules.live_monitoring."
            "screenshot_retention."
            "delete_object"
        ),
        fake_delete_object,
    )

    session = FakeSession(
        [
            item,
        ]
    )

    service = (
        ScreenshotRetentionService(
            session
        )
    )

    result = await service.cleanup(
        retention_days=30,
        now=NOW,
    )

    assert deleted_objects == [
        "screenshots/example.png",
    ]

    assert session.deleted == [
        item,
    ]

    assert result.deleted == 1


@pytest.mark.asyncio
async def test_storage_failure_preserves_database_record(
    monkeypatch,
):
    item = _item(
        object_key=(
            "screenshots/failure.png"
        )
    )

    def fake_delete_object(
        *,
        object_key: str,
    ) -> None:
        del object_key

        raise RuntimeError(
            "storage unavailable"
        )

    monkeypatch.setattr(
        (
            "app.modules.live_monitoring."
            "screenshot_retention."
            "delete_object"
        ),
        fake_delete_object,
    )

    session = FakeSession(
        [
            item,
        ]
    )

    service = (
        ScreenshotRetentionService(
            session
        )
    )

    result = await service.cleanup(
        retention_days=30,
        now=NOW,
    )

    assert session.deleted == []

    assert result.deleted == 0

    assert (
        result.storage_failures
        == 1
    )


@pytest.mark.asyncio
async def test_cleanup_reports_more_batches():
    first = _item(
        object_key=None
    )

    second = _item(
        object_key=None
    )

    session = FakeSession(
        [
            first,
            second,
        ]
    )

    service = (
        ScreenshotRetentionService(
            session
        )
    )

    result = await service.cleanup(
        retention_days=30,
        now=NOW,
        limit=1,
    )

    assert result.scanned == 1

    assert result.deleted == 1

    assert result.has_more is True