from __future__ import annotations

import inspect

from app.modules.ai_productivity.enums import (
    AIProductivitySource,
)
from app.modules.ai_productivity.router import (
    run_ai_productivity,
)
from app.modules.ai_productivity.schemas import (
    AIProductivityRequest,
)
from app.modules.workspace_permissions.permissions import (
    WorkspacePermission,
)


def test_ai_productivity_permission_exists():
    assert (
        WorkspacePermission
        .AI_PRODUCTIVITY_USE
        .value
        == "ai_productivity.use"
    )


def test_ai_productivity_default_sources_are_bounded():
    field = (
        AIProductivityRequest
        .model_fields[
            "sources"
        ]
    )

    factory = (
        field.default_factory
    )

    assert (
        factory is not None
    )

    sources = factory()

    assert set(
        sources
    ) == {
        AIProductivitySource.GOALS,
        AIProductivitySource.NOTES,
        AIProductivitySource.KNOWLEDGE,
    }


def test_ai_run_requires_workspace_permission():
    source = inspect.getsource(
        run_ai_productivity
    )

    assert (
        "AI_PRODUCTIVITY_USE"
        in source
    )


def test_ai_request_has_item_limit():
    fields = (
        AIProductivityRequest
        .model_fields
    )

    assert (
        "max_items_per_source"
        in fields
    )