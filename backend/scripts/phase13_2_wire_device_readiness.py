from __future__ import annotations

import re
from pathlib import Path


# =========================================================
# PATHS
# =========================================================


ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)


TARGET = (
    ROOT
    / "app"
    / "modules"
    / "tenant_api"
    / "router.py"
)


# =========================================================
# IMPORTS
# =========================================================


READINESS_IMPORT = """from app.modules.devices.readiness_router import (
    DEVICE_READINESS_SCOPE_STATE_KEY,
    router as device_readiness_router,
)
"""


TENANT_IMPORT = """from app.db.tenant_dependency import (
    TenantScope,
)
"""


REQUEST_IMPORT = """from fastapi import Request
"""


# =========================================================
# BINDER
# =========================================================


BINDER_BLOCK = """
# =========================================================
# PHASE 13.2 — DEVICE READINESS SCOPE BINDER
# =========================================================


async def bind_device_readiness_scope(
    request: Request,
    scope: TenantScope,
) -> None:
    setattr(
        request.state,
        DEVICE_READINESS_SCOPE_STATE_KEY,
        scope,
    )


"""


# =========================================================
# INCLUDE
# =========================================================


INCLUDE_BLOCK = """
# =========================================================
# PHASE 13.2 — DEVICE READINESS
# =========================================================

router.include_router(
    device_readiness_router,
    dependencies=[
        Depends(
            bind_device_readiness_scope
        )
    ],
)


"""


# =========================================================
# CLEANUP
# =========================================================


def _remove_old_readiness_sections(
    source: str,
) -> str:
    # Old executable includes.
    source = re.sub(
        r"""
router\.include_router\s*\(
\s*device_readiness_router\s*,?\s*
\)\s*
""",
        "",
        source,
        flags=(
            re.MULTILINE
            | re.VERBOSE
        ),
    )

    # New executable include, so script remains idempotent.
    source = re.sub(
        r"""
router\.include_router\s*\(
\s*device_readiness_router\s*,
\s*dependencies\s*=\s*\[
\s*Depends\s*\(
\s*bind_device_readiness_scope\s*
\)
\s*\]
\s*,?\s*
\)\s*
""",
        "",
        source,
        flags=(
            re.MULTILINE
            | re.VERBOSE
        ),
    )

    # Binder from an earlier execution.
    source = re.sub(
        r"""
async\s+def\s+bind_device_readiness_scope\s*\(
\s*request\s*:\s*Request\s*,
\s*scope\s*:\s*TenantScope\s*,
\s*\)\s*->\s*None\s*:
\s*setattr\s*\(
\s*request\.state\s*,
\s*DEVICE_READINESS_SCOPE_STATE_KEY\s*,
\s*scope\s*,
\s*\)
\s*
""",
        "",
        source,
        flags=(
            re.MULTILINE
            | re.VERBOSE
        ),
    )

    # Remove duplicate/readiness-only phase comments left from the
    # previous wiring attempts.
    source = re.sub(
        r"""
\#\s*=+\s*\n
\#\s*PHASE\s+13\.2\s+[—-]\s+DEVICE\s+READINESS(?:\s+SCOPE\s+BINDER)?\s*\n
\#\s*=+\s*\n
""",
        "",
        source,
        flags=(
            re.MULTILINE
            | re.VERBOSE
        ),
    )

    return source


# =========================================================
# IMPORT HELPERS
# =========================================================


def _ensure_readiness_import(
    source: str,
) -> str:
    if (
        "router as device_readiness_router"
        in source
        and "DEVICE_READINESS_SCOPE_STATE_KEY"
        in source
    ):
        return source

    # Remove earlier readiness import first.
    source = re.sub(
        r"""
from\s+app\.modules\.devices\.readiness_router\s+import\s*\(
.*?
\)\s*
""",
        "",
        source,
        flags=(
            re.MULTILINE
            | re.DOTALL
            | re.VERBOSE
        ),
    )

    router_assignment = re.search(
        r"^router\s*=\s*APIRouter\s*\(\s*\)",
        source,
        flags=re.MULTILINE,
    )

    if router_assignment is None:
        raise RuntimeError(
            "Could not locate tenant "
            "router assignment."
        )

    position = router_assignment.start()

    return (
        source[:position]
        + READINESS_IMPORT
        + "\n"
        + source[position:]
    )


def _ensure_tenant_import(
    source: str,
) -> str:
    if (
        "from app.db.tenant_dependency import"
        in source
        and "TenantScope"
        in source
    ):
        return source

    router_assignment = re.search(
        r"^router\s*=\s*APIRouter\s*\(\s*\)",
        source,
        flags=re.MULTILINE,
    )

    if router_assignment is None:
        raise RuntimeError(
            "Could not locate tenant "
            "router assignment."
        )

    position = router_assignment.start()

    return (
        source[:position]
        + TENANT_IMPORT
        + "\n"
        + source[position:]
    )


def _ensure_request_import(
    source: str,
) -> str:
    # Existing grouped fastapi import may already expose Request.
    if re.search(
        r"\bRequest\b",
        source,
    ):
        return source

    router_assignment = re.search(
        r"^router\s*=\s*APIRouter\s*\(\s*\)",
        source,
        flags=re.MULTILINE,
    )

    if router_assignment is None:
        raise RuntimeError(
            "Could not locate tenant "
            "router assignment."
        )

    position = router_assignment.start()

    return (
        source[:position]
        + REQUEST_IMPORT
        + "\n"
        + source[position:]
    )


# =========================================================
# INSERT BINDER
# =========================================================


def _insert_binder(
    source: str,
) -> str:
    assignment = re.search(
        r"^router\s*=\s*APIRouter\s*\(\s*\)",
        source,
        flags=re.MULTILINE,
    )

    if assignment is None:
        raise RuntimeError(
            "Could not locate tenant "
            "router assignment."
        )

    position = assignment.end()

    return (
        source[:position]
        + "\n"
        + BINDER_BLOCK
        + source[position:]
    )


# =========================================================
# INSERT INCLUDE AT END
# =========================================================


def _insert_final_include(
    source: str,
) -> str:
    """
    Register readiness after all existing tenant child routers have
    been assembled.

    Prefer insertion immediately before __all__ when present.
    Otherwise append to EOF.
    """

    all_match = re.search(
        r"^__all__\s*=",
        source,
        flags=re.MULTILINE,
    )

    if all_match is not None:
        position = all_match.start()

        return (
            source[:position]
            + INCLUDE_BLOCK
            + source[position:]
        )

    return (
        source.rstrip()
        + "\n"
        + INCLUDE_BLOCK
    )


# =========================================================
# VERIFY
# =========================================================


def _verify(
    source: str,
) -> None:
    if (
        source.count(
            "router as device_readiness_router"
        )
        != 1
    ):
        raise RuntimeError(
            "Expected exactly one readiness import."
        )

    if (
        source.count(
            "async def bind_device_readiness_scope"
        )
        != 1
    ):
        raise RuntimeError(
            "Expected exactly one readiness scope binder."
        )

    include_pattern = re.compile(
        r"""
router\.include_router\s*\(
\s*device_readiness_router\s*,
\s*dependencies\s*=\s*\[
""",
        flags=(
            re.MULTILINE
            | re.VERBOSE
        ),
    )

    if (
        len(
            include_pattern.findall(
                source
            )
        )
        != 1
    ):
        raise RuntimeError(
            "Expected exactly one final "
            "readiness router include."
        )


# =========================================================
# MAIN
# =========================================================


def main() -> None:
    if not TARGET.is_file():
        raise RuntimeError(
            f"Missing tenant router: {TARGET}"
        )

    source = TARGET.read_text(
        encoding="utf-8"
    )

    source = (
        _remove_old_readiness_sections(
            source
        )
    )

    source = _ensure_readiness_import(
        source
    )

    source = _ensure_tenant_import(
        source
    )

    source = _ensure_request_import(
        source
    )

    source = _insert_binder(
        source
    )

    source = _insert_final_include(
        source
    )

    _verify(
        source
    )

    TARGET.write_text(
        source,
        encoding="utf-8",
    )

    print(
        "PASS Phase 13.2 readiness "
        "late-bound router wiring complete"
    )


if __name__ == "__main__":
    main()