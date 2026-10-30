from __future__ import annotations

import ast
from pathlib import Path
from typing import Any


ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)


TENANT_VERSIONS = (
    ROOT
    / "migrations"
    / "tenant"
    / "versions"
)


# =========================================================
# AST HELPERS
# =========================================================


def _literal_assignment(
    source: str,
    name: str,
) -> Any:
    tree = ast.parse(
        source
    )

    for node in tree.body:

        # -------------------------------------------------
        # name = value
        # -------------------------------------------------

        if isinstance(
            node,
            ast.Assign,
        ):
            for target in node.targets:
                if (
                    isinstance(
                        target,
                        ast.Name,
                    )
                    and target.id
                    == name
                ):
                    try:
                        return ast.literal_eval(
                            node.value
                        )

                    except (
                        ValueError,
                        TypeError,
                    ):
                        return None

        # -------------------------------------------------
        # name: str = value
        # -------------------------------------------------

        if isinstance(
            node,
            ast.AnnAssign,
        ):
            if (
                isinstance(
                    node.target,
                    ast.Name,
                )
                and node.target.id
                == name
            ):
                if node.value is None:
                    return None

                try:
                    return ast.literal_eval(
                        node.value
                    )

                except (
                    ValueError,
                    TypeError,
                ):
                    return None

    return None


# =========================================================
# MIGRATION GRAPH
# =========================================================


def tenant_revision_parents() -> dict[
    str,
    tuple[str, ...],
]:
    """
    Build:

        revision -> parent revisions

    directly from migrations/tenant/versions.

    Supports:

        down_revision = "abc"

        down_revision: str = "abc"

        down_revision = ("a", "b")

        down_revision = None
    """

    graph: dict[
        str,
        tuple[str, ...],
    ] = {}

    for path in TENANT_VERSIONS.glob(
        "*.py"
    ):
        source = path.read_text(
            encoding="utf-8"
        )

        revision = (
            _literal_assignment(
                source,
                "revision",
            )
        )

        if not isinstance(
            revision,
            str,
        ):
            continue

        down_revision = (
            _literal_assignment(
                source,
                "down_revision",
            )
        )

        if down_revision is None:
            parents: tuple[
                str,
                ...,
            ] = ()

        elif isinstance(
            down_revision,
            str,
        ):
            parents = (
                down_revision,
            )

        elif isinstance(
            down_revision,
            (
                tuple,
                list,
            ),
        ):
            parents = tuple(
                str(
                    value
                )
                for value
                in down_revision
            )

        else:
            raise AssertionError(
                "Unsupported down_revision "
                f"for {revision}: "
                f"{down_revision!r}"
            )

        graph[
            revision
        ] = parents

    return graph


# =========================================================
# ANCESTRY
# =========================================================


def revision_is_ancestor(
    *,
    ancestor: str,
    descendant: str,
) -> bool:
    """
    True when ancestor == descendant or ancestor appears anywhere
    in descendant's migration ancestry.
    """

    graph = (
        tenant_revision_parents()
    )

    if ancestor == descendant:
        return True

    if descendant not in graph:
        return False

    visited: set[str] = set()

    pending = [
        descendant
    ]

    while pending:
        current = pending.pop()

        if current in visited:
            continue

        visited.add(
            current
        )

        for parent in graph.get(
            current,
            (),
        ):
            if parent == ancestor:
                return True

            if parent not in visited:
                pending.append(
                    parent
                )

    return False


# =========================================================
# ASSERTION
# =========================================================


def assert_revision_present_in_runtime_chain(
    *,
    required_revision: str,
    current_revision: str,
) -> None:
    graph = (
        tenant_revision_parents()
    )

    assert (
        required_revision
        in graph
    ), (
        "Required tenant revision "
        f"{required_revision!r} "
        "is missing from migration files."
    )

    assert (
        current_revision
        in graph
    ), (
        "Runtime tenant revision "
        f"{current_revision!r} "
        "is missing from migration files."
    )

    assert revision_is_ancestor(
        ancestor=(
            required_revision
        ),
        descendant=(
            current_revision
        ),
    ), (
        "Required tenant revision "
        f"{required_revision!r} "
        "is not an ancestor of runtime "
        f"revision {current_revision!r}."
    )


__all__ = [
    "tenant_revision_parents",
    "revision_is_ancestor",
    "assert_revision_present_in_runtime_chain",
]