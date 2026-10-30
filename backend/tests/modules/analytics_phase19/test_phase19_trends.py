from __future__ import annotations

import ast
import inspect
import textwrap

from app.modules.analytics.service import (
    AnalyticsService,
)


def _method_ast(
    method,
) -> ast.AST:
    source = inspect.getsource(
        method
    )

    return ast.parse(
        textwrap.dedent(
            source
        )
    )


def test_trends_use_all_daily_sources():
    source = inspect.getsource(
        AnalyticsService.trends
    )

    required_sources = [
        "activity_daily",
        "attendance_daily",
        "app_daily",
        "website_daily",
        "goals_daily",
    ]

    for source_name in required_sources:
        assert (
            source_name
            in source
        )


def test_trends_do_not_parallelize_same_session():
    tree = _method_ast(
        AnalyticsService.trends
    )

    for node in ast.walk(
        tree
    ):
        if not isinstance(
            node,
            ast.Call,
        ):
            continue

        function = node.func

        if not isinstance(
            function,
            ast.Attribute,
        ):
            continue

        if (
            function.attr
            != "gather"
        ):
            continue

        owner = function.value

        if (
            isinstance(
                owner,
                ast.Name,
            )
            and owner.id
            == "asyncio"
        ):
            raise AssertionError(
                "AnalyticsService.trends "
                "must not call "
                "asyncio.gather() with "
                "queries sharing the same "
                "AsyncSession."
            )


def test_expected_trend_keys_exist():
    source = inspect.getsource(
        AnalyticsService.trends
    )

    expected = [
        '"activity_events"',
        '"attendance_records"',
        '"app_seconds"',
        '"website_seconds"',
        '"goals_created"',
    ]

    for key in expected:
        assert (
            key
            in source
        )