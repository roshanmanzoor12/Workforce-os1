from __future__ import annotations

from pathlib import Path


TARGET = Path(
    "app/modules/live_monitoring/service.py"
)


IMPORT_BLOCK = """from app.modules.live_monitoring.live_screen_readiness import (
    require_live_screen_ready,
)
"""


REQUEST_ANCHOR = """        device = await self._device(
            access=access,
            device_id=payload.device_id,
        )

        now = self._now()
"""


REQUEST_REPLACEMENT = """        device = await self._device(
            access=access,
            device_id=payload.device_id,
        )

        require_live_screen_ready(
            device=device,
            now=self._now(),
        )

        now = self._now()
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

    # =====================================================
    # IMPORT
    # =====================================================

    if (
        "require_live_screen_ready"
        not in source
    ):
        anchor = (
            "from app.modules.live_monitoring.models import ("
        )

        if anchor not in source:
            raise RuntimeError(
                "Could not find live_monitoring "
                "models import anchor."
            )

        source = source.replace(
            anchor,
            (
                IMPORT_BLOCK
                + anchor
            ),
            1,
        )

    # =====================================================
    # REQUEST GUARD
    # =====================================================

    if (
        "require_live_screen_ready(\n"
        "            device=device,"
        not in source
    ):
        if REQUEST_ANCHOR not in source:
            raise RuntimeError(
                "Could not find exact "
                "request_live_screen device anchor."
            )

        source = source.replace(
            REQUEST_ANCHOR,
            REQUEST_REPLACEMENT,
            1,
        )

    # =====================================================
    # VALIDATION
    # =====================================================

    if (
        source.count(
            "require_live_screen_ready"
        )
        < 2
    ):
        raise RuntimeError(
            "Live Screen readiness wiring "
            "is incomplete."
        )

    if source != original:
        backup = TARGET.with_suffix(
            ".py.phase16_backup"
        )

        if not backup.exists():
            backup.write_text(
                original,
                encoding="utf-8",
            )

        TARGET.write_text(
            source,
            encoding="utf-8",
        )

    print(
        "PASS Phase 16 Live Screen "
        "readiness wiring complete"
    )


if __name__ == "__main__":
    main()