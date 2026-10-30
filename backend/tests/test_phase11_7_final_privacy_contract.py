from __future__ import annotations

from pathlib import Path


SOURCE_ROOTS = [
    Path(
        "app/modules/employees"
    ),
    Path(
        "app/modules/attendance"
    ),
    Path(
        "app/modules/tenant_api"
    ),
]


FORBIDDEN_IMPLEMENTATION_TOKENS = [
    "keylogger(",
    "start_keylogger",
    "enable_keylogging",
    "capture_keystrokes",
    "record_keystrokes",
    "clipboard.read",
    "clipboard.get",
    "capture_clipboard",
    "read_clipboard",
    "typed_text =",
    "capture_typed_text",
    "record_typed_text",
    "capture_password",
    "record_password",
    "mouse_coordinates =",
    "capture_mouse_coordinates",
    "stealth_mode = true",
    "stealth_mode=true",
]


def iter_python_files():
    for root in SOURCE_ROOTS:
        if not root.exists():
            continue

        yield from root.rglob(
            "*.py"
        )


def test_phase11_7_has_no_invasive_monitoring_implementation(
) -> None:
    """
    Phase 11.7 may explicitly declare privacy capabilities as false.

    Example:

        "keylogging": False

    That is allowed.

    What is forbidden here is actual implementation or enablement of
    invasive monitoring behavior.
    """

    for path in iter_python_files():
        text = path.read_text(
            encoding="utf-8",
            errors="ignore",
        ).lower()

        for token in (
            FORBIDDEN_IMPLEMENTATION_TOKENS
        ):
            assert token not in text, (
                "Forbidden invasive monitoring "
                f"implementation token {token!r} "
                f"found in {path}"
            )


def test_phase11_7_privacy_contract_disables_invasive_features(
) -> None:
    contract_path = Path(
        "app/modules/tenant_api/"
        "phase11_7_contract.py"
    )

    assert contract_path.exists()

    namespace: dict[
        str,
        object,
    ] = {}

    exec(
        contract_path.read_text(
            encoding="utf-8"
        ),
        namespace,
    )

    contract = namespace[
        "PHASE_11_7_TENANT_CONTRACT"
    ]

    privacy = contract[
        "privacy"
    ]

    assert (
        privacy["keylogging"]
        is False
    )

    assert (
        privacy["clipboard_capture"]
        is False
    )

    assert (
        privacy["typed_text_capture"]
        is False
    )

    assert (
        privacy["password_capture"]
        is False
    )

    assert (
        privacy["mouse_coordinates"]
        is False
    )


def test_phase11_7_attendance_is_source_attributed(
) -> None:
    attendance_models = Path(
        "app/modules/attendance/"
        "models.py"
    ).read_text(
        encoding="utf-8",
    )

    assert (
        "source"
        in attendance_models
    )

    assert (
        "actor_user_id"
        in attendance_models
    )


def test_phase11_7_has_no_stealth_attendance_mode(
) -> None:
    attendance_root = Path(
        "app/modules/attendance"
    )

    for path in attendance_root.rglob(
        "*.py"
    ):
        text = path.read_text(
            encoding="utf-8",
            errors="ignore",
        ).lower()

        assert (
            "stealth_mode = true"
            not in text
        )

        assert (
            "stealth_mode=true"
            not in text
        )