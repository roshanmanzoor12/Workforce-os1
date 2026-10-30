from __future__ import annotations

import uuid
from datetime import date

import pytest

from app.modules.payroll.lifecycle import (
    PayrollLifecycleError,
    PayrollRunLifecycle,
)
from app.modules.payroll.models import (
    PayrollRun,
    PayrollRunStatus,
)


def _run(
    state: PayrollRunStatus,
) -> PayrollRun:
    return PayrollRun(
        id=uuid.uuid4(),
        period_start=date(
            2026,
            9,
            1,
        ),
        period_end=date(
            2026,
            9,
            30,
        ),
        currency="PKR",
        status=state,
        policy_version=(
            "phase12.3-v1"
        ),
    )


def test_draft_is_mutable():
    PayrollRunLifecycle.require_mutable(
        _run(
            PayrollRunStatus.DRAFT
        )
    )


def test_review_is_mutable():
    PayrollRunLifecycle.require_mutable(
        _run(
            PayrollRunStatus.REVIEW
        )
    )


@pytest.mark.parametrize(
    "state",
    [
        PayrollRunStatus.APPROVED,
        PayrollRunStatus.LOCKED,
        PayrollRunStatus.PAID,
        PayrollRunStatus.VOID,
    ],
)
def test_final_states_are_not_mutable(
    state,
):
    with pytest.raises(
        PayrollLifecycleError
    ):
        PayrollRunLifecycle.require_mutable(
            _run(
                state
            )
        )


def test_paid_is_terminal():
    assert (
        PayrollRunStatus.PAID
        in (
            PayrollRunLifecycle
            .TERMINAL_STATUSES
        )
    )


def test_void_is_terminal():
    assert (
        PayrollRunStatus.VOID
        in (
            PayrollRunLifecycle
            .TERMINAL_STATUSES
        )
    )