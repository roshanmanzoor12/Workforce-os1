from __future__ import annotations

from pathlib import Path


ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)


ROUTER_PATH = (
    ROOT
    / "app"
    / "modules"
    / "tenant_api"
    / "router.py"
)


def main() -> None:
    source = (
        ROUTER_PATH
        .read_text(
            encoding="utf-8"
        )
    )

    import_needle = (
        "from app.modules.leave.router import (\n"
        "    router as leave_router,\n"
        ")\n"
    )

    import_block = (
        import_needle
        + "from app.modules.leave.integration_router import (\n"
        + "    router as leave_integration_router,\n"
        + ")\n"
    )

    if (
        "leave_integration_router"
        not in source
    ):
        if import_needle not in source:
            raise RuntimeError(
                "Leave router import "
                "was not found."
            )

        source = source.replace(
            import_needle,
            import_block,
            1,
        )

        print(
            "PATCH leave integration "
            "router import"
        )

    else:
        print(
            "SKIP leave integration "
            "router import"
        )

    include_needle = (
        "router.include_router(\n"
        "    leave_router\n"
        ")\n"
    )

    include_block = (
        include_needle
        + "\n"
        + "router.include_router(\n"
        + "    leave_integration_router\n"
        + ")\n"
    )

    if (
        "router.include_router(\n"
        "    leave_integration_router\n"
        ")"
        not in source
    ):
        if include_needle not in source:
            raise RuntimeError(
                "Leave router registration "
                "was not found."
            )

        source = source.replace(
            include_needle,
            include_block,
            1,
        )

        print(
            "PATCH leave integration "
            "router registration"
        )

    else:
        print(
            "SKIP leave integration "
            "router registration"
        )

    ROUTER_PATH.write_text(
        source,
        encoding="utf-8",
    )

    print()
    print(
        "PASS Phase 12.2 integration "
        "router wiring"
    )


if __name__ == "__main__":
    main()