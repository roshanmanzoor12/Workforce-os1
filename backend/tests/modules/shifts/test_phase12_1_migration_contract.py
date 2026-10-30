from __future__ import annotations

import ast
from pathlib import Path


MIGRATION_PATH = (
    Path("migrations")
    / "tenant"
    / "versions"
    / (
        "l2g3h4i5j6k7_"
        "phase12_1_shifts_holidays.py"
    )
)


def migration_text() -> str:
    return MIGRATION_PATH.read_text(
        encoding="utf-8"
    )


def migration_ast() -> ast.Module:
    return ast.parse(
        migration_text()
    )


def string_constants() -> set[str]:
    """
    Collect Python string constants after AST parsing.

    Important:

    Python automatically concatenates adjacent literals:

        "abc_"
        "def"

    into:

        "abc_def"

    Therefore AST inspection is the correct way to validate
    migration identifiers that are formatted across lines.
    """

    tree = migration_ast()

    values: set[str] = set()

    for node in ast.walk(
        tree
    ):
        if (
            isinstance(
                node,
                ast.Constant,
            )
            and isinstance(
                node.value,
                str,
            )
        ):
            values.add(
                node.value
            )

    return values


def test_migration_exists():
    assert MIGRATION_PATH.exists()


def test_migration_is_valid_python():
    migration_ast()


def test_migration_revision_chain():
    constants = (
        string_constants()
    )

    assert (
        "l2g3h4i5j6k7"
        in constants
    )

    assert (
        "k1f2g3h4i5j6"
        in constants
    )


def test_all_required_tables_exist():
    constants = (
        string_constants()
    )

    required = {
        "shift_templates",
        "shift_working_days",
        "shift_assignments",
        "schedule_exceptions",
        "schedule_publications",
        "holidays",
    }

    assert required.issubset(
        constants
    )


def test_shift_policy_columns_exist():
    constants = (
        string_constants()
    )

    required = {
        "break_minutes",
        "standard_paid_minutes",
        "grace_before_minutes",
        "grace_after_minutes",
        "overtime_after_minutes",
        "is_overnight",
        "is_active",
    }

    assert required.issubset(
        constants
    )


def test_publication_enum_matches_model():
    constants = (
        string_constants()
    )

    required = {
        "DRAFT",
        "PUBLISHED",
        "CANCELLED",
    }

    assert required.issubset(
        constants
    )


def test_assignment_enum_matches_model():
    constants = (
        string_constants()
    )

    required = {
        "EMPLOYEE",
        "TEAM",
    }

    assert required.issubset(
        constants
    )


def test_exception_enum_matches_model():
    constants = (
        string_constants()
    )

    required = {
        "OFF_DAY",
        "CUSTOM_SHIFT",
    }

    assert required.issubset(
        constants
    )


def test_holiday_enum_matches_model():
    constants = (
        string_constants()
    )

    required = {
        "PAID",
        "UNPAID",
    }

    assert required.issubset(
        constants
    )


def test_shift_assignment_fk_is_restrict():
    constants = (
        string_constants()
    )

    assert (
        "RESTRICT"
        in constants
    )


def test_model_index_names_are_present():
    constants = (
        string_constants()
    )

    expected = {
        "ix_shift_templates_active",
        "ix_shift_working_days_shift",
        "ix_shift_assignments_target",
        "ix_shift_assignments_effective",
        "ix_schedule_exceptions_date",
        (
            "ix_schedule_exceptions_"
            "employee_id"
        ),
        (
            "ix_schedule_publications_"
            "range"
        ),
        "ix_holidays_date_active",
    }

    assert expected.issubset(
        constants
    )


def test_model_unique_constraint_names_are_present():
    constants = (
        string_constants()
    )

    expected = {
        "uq_shift_templates_name",
        (
            "uq_shift_working_days_"
            "shift_weekday"
        ),
        (
            "uq_schedule_exception_"
            "employee_date"
        ),
        "uq_holidays_date_name",
    }

    assert expected.issubset(
        constants
    )


def test_expected_enum_type_names_are_present():
    constants = (
        string_constants()
    )

    expected = {
        (
            "shift_assignment_"
            "target_type"
        ),
        (
            "schedule_exception_type"
        ),
        (
            "schedule_publication_"
            "status"
        ),
        "holiday_treatment",
    }

    assert expected.issubset(
        constants
    )


def test_downgrade_exists():
    tree = migration_ast()

    function_names = {
        node.name
        for node
        in tree.body
        if isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        )
    }

    assert "upgrade" in function_names
    assert "downgrade" in function_names