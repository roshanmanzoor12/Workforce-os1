from __future__ import annotations

import uuid
from datetime import (
    date,
    datetime,
    timezone,
)

import pytest

from app.modules.payroll.lifecycle import (
    PayrollLifecycleError,
    PayrollRunLifecycle,
)
from app.modules.payroll.models import (
    PayrollRun,
    PayrollRunStatus,
)
from app.modules.payroll.router import (
    router,
)


def route_paths() -> set[str]:
    return {
        route.path
        for route in router.routes
        if hasattr(
            route,
            "path",
        )
    }


def build_run(
    status: PayrollRunStatus,
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
        cutoff_date=date(
            2026,
            9,
            30,
        ),
        currency="PKR",
        status=status,
        policy_version=(
            "phase12.3-v1"
        ),
    )


def test_compensation_api_routes():
    paths = route_paths()

    assert (
        "/workspaces/{workspace_id}"
        "/compensation/contracts"
        in paths
    )

    assert (
        "/workspaces/{workspace_id}"
        "/compensation/contracts/"
        "{contract_id}"
        in paths
    )


def test_payroll_run_routes():
    paths = route_paths()

    assert (
        "/workspaces/{workspace_id}"
        "/payroll/runs"
        in paths
    )

    assert (
        "/workspaces/{workspace_id}"
        "/payroll/runs/{run_id}/employees"
        in paths
    )

    assert (
        "/workspaces/{workspace_id}"
        "/payroll/runs/{run_id}/adjustments"
        in paths
    )


def test_payroll_state_routes():
    paths = route_paths()

    assert (
        "/workspaces/{workspace_id}"
        "/payroll/runs/{run_id}/approve"
        in paths
    )

    assert (
        "/workspaces/{workspace_id}"
        "/payroll/runs/{run_id}/lock"
        in paths
    )

    assert (
        "/workspaces/{workspace_id}"
        "/payroll/runs/{run_id}/mark-paid"
        in paths
    )


def test_draft_and_review_are_mutable():
    assert (
        PayrollRunLifecycle
        .is_mutable(
            build_run(
                PayrollRunStatus.DRAFT
            )
        )
    )

    assert (
        PayrollRunLifecycle
        .is_mutable(
            build_run(
                PayrollRunStatus.REVIEW
            )
        )
    )


def test_locked_run_is_not_mutable():
    run = build_run(
        PayrollRunStatus.LOCKED
    )

    with pytest.raises(
        PayrollLifecycleError
    ):
        (
            PayrollRunLifecycle
            .require_mutable(
                run
            )
        )


def test_review_to_approved():
    run = build_run(
        PayrollRunStatus.REVIEW
    )

    actor = uuid.uuid4()

    now = datetime(
        2026,
        9,
        29,
        tzinfo=timezone.utc,
    )

    PayrollRunLifecycle.approve(
        run,
        actor_user_id=actor,
        now=now,
    )

    assert (
        run.status
        == PayrollRunStatus.APPROVED
    )

    assert (
        run.approved_by_user_id
        == actor
    )

    assert run.approved_at == now


def test_approved_to_locked():
    run = build_run(
        PayrollRunStatus.APPROVED
    )

    actor = uuid.uuid4()

    PayrollRunLifecycle.lock(
        run,
        actor_user_id=actor,
    )

    assert (
        run.status
        == PayrollRunStatus.LOCKED
    )

    assert (
        run.locked_by_user_id
        == actor
    )


def test_locked_to_paid():
    run = build_run(
        PayrollRunStatus.LOCKED
    )

    actor = uuid.uuid4()

    PayrollRunLifecycle.mark_paid(
        run,
        actor_user_id=actor,
    )

    assert (
        run.status
        == PayrollRunStatus.PAID
    )

    assert (
        run.paid_by_user_id
        == actor
    )


def test_cannot_skip_review_to_lock():
    run = build_run(
        PayrollRunStatus.REVIEW
    )

    with pytest.raises(
        PayrollLifecycleError
    ):
        PayrollRunLifecycle.lock(
            run,
            actor_user_id=(
                uuid.uuid4()
            ),
        )