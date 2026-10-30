from __future__ import annotations

from pathlib import Path


TARGET = Path(
    "app/modules/tenant_api/router.py"
)


IMPORT_BLOCK = """from app.modules.employee_monitoring_detail.router import (
    router as employee_monitoring_detail_router,
)
"""


INCLUDE_BLOCK = """
# =========================================================
# PHASE 15 — EMPLOYEE MONITORING DETAIL
# =========================================================

router.include_router(
    employee_monitoring_detail_router
)

"""


def main() -> None:
    if not TARGET.exists():
        raise RuntimeError(
            f"Missing target: {TARGET}"
        )

    source = TARGET.read_text(
        encoding="utf-8"
    )

    original = source

    # -----------------------------------------------------
    # IMPORT
    # -----------------------------------------------------

    if (
        "employee_monitoring_detail_router"
        not in source
    ):
        anchor = (
            "\nrouter = APIRouter()"
        )

        if anchor not in source:
            raise RuntimeError(
                "Could not locate tenant "
                "router assignment."
            )

        source = source.replace(
            anchor,
            (
                "\n"
                + IMPORT_BLOCK
                + anchor
            ),
            1,
        )

    # -----------------------------------------------------
    # INCLUDE
    # -----------------------------------------------------

    include_signature = (
        "router.include_router(\n"
        "    employee_monitoring_detail_router"
    )

    if include_signature not in source:
        anchor = "\n__all__ = ["

        if anchor not in source:
            raise RuntimeError(
                "Could not locate tenant "
                "router __all__ block."
            )

        source = source.replace(
            anchor,
            (
                "\n"
                + INCLUDE_BLOCK
                + "__all__ = ["
            ),
            1,
        )

    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    if (
        source.count(
            "router as "
            "employee_monitoring_detail_router"
        )
        != 1
    ):
        raise RuntimeError(
            "Employee monitoring detail "
            "router import count is invalid."
        )

    if (
        source.count(
            "employee_monitoring_detail_router"
        )
        < 2
    ):
        raise RuntimeError(
            "Employee monitoring detail "
            "router include is missing."
        )

    if source != original:
        backup = TARGET.with_suffix(
            ".py.phase15_backup"
        )

        backup.write_text(
            original,
            encoding="utf-8",
        )

        TARGET.write_text(
            source,
            encoding="utf-8",
        )

    print(
        "PASS Phase 15 employee monitoring "
        "detail router wiring complete"
    )


if __name__ == "__main__":
    main()