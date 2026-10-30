from __future__ import annotations

import uuid
from datetime import (
    datetime,
    timezone,
)

from app.modules.payroll.models import (
    PayrollRun,
    PayrollRunStatus,
)


class PayrollLifecycleError(
    RuntimeError
):
    pass


def utc_now() -> datetime:
    return datetime.now(
        timezone.utc
    )


class PayrollRunLifecycle:
    """
    Central state transition rules.

    Allowed lifecycle:

        DRAFT
          |
          v
        REVIEW
          |
          v
        APPROVED
          |
          v
        LOCKED
          |
          v
        PAID

    VOID is terminal.

    Draft and Review remain mutable.
    Approved, Locked, Paid and Void are immutable to ordinary
    recalculation/adjustment flows.
    """

    MUTABLE_STATUSES = frozenset(
        {
            PayrollRunStatus.DRAFT,
            PayrollRunStatus.REVIEW,
        }
    )

    TERMINAL_STATUSES = frozenset(
        {
            PayrollRunStatus.PAID,
            PayrollRunStatus.VOID,
        }
    )

    @classmethod
    def is_mutable(
        cls,
        run: PayrollRun,
    ) -> bool:
        return (
            run.status
            in cls.MUTABLE_STATUSES
        )

    @classmethod
    def require_mutable(
        cls,
        run: PayrollRun,
    ) -> None:
        if cls.is_mutable(
            run
        ):
            return

        raise PayrollLifecycleError(
            "Payroll run is no longer "
            "mutable."
        )

    @staticmethod
    def move_to_review(
        run: PayrollRun,
    ) -> None:
        if run.status == (
            PayrollRunStatus.DRAFT
        ):
            run.status = (
                PayrollRunStatus.REVIEW
            )

            return

        if run.status == (
            PayrollRunStatus.REVIEW
        ):
            return

        raise PayrollLifecycleError(
            "Only Draft payroll can "
            "enter Review."
        )

    @staticmethod
    def approve(
        run: PayrollRun,
        *,
        actor_user_id: uuid.UUID,
        now: datetime | None = None,
    ) -> None:
        if run.status != (
            PayrollRunStatus.REVIEW
        ):
            raise PayrollLifecycleError(
                "Only Review payroll "
                "can be approved."
            )

        current = (
            now
            or utc_now()
        )

        run.status = (
            PayrollRunStatus.APPROVED
        )

        run.approved_by_user_id = (
            actor_user_id
        )

        run.approved_at = current

    @staticmethod
    def lock(
        run: PayrollRun,
        *,
        actor_user_id: uuid.UUID,
        now: datetime | None = None,
    ) -> None:
        if run.status != (
            PayrollRunStatus.APPROVED
        ):
            raise PayrollLifecycleError(
                "Only Approved payroll "
                "can be locked."
            )

        current = (
            now
            or utc_now()
        )

        run.status = (
            PayrollRunStatus.LOCKED
        )

        run.locked_by_user_id = (
            actor_user_id
        )

        run.locked_at = current

    @staticmethod
    def mark_paid(
        run: PayrollRun,
        *,
        actor_user_id: uuid.UUID,
        now: datetime | None = None,
    ) -> None:
        if run.status != (
            PayrollRunStatus.LOCKED
        ):
            raise PayrollLifecycleError(
                "Only Locked payroll "
                "can be marked paid."
            )

        current = (
            now
            or utc_now()
        )

        run.status = (
            PayrollRunStatus.PAID
        )

        run.paid_by_user_id = (
            actor_user_id
        )

        run.paid_at = current


__all__ = [
    "PayrollLifecycleError",
    "PayrollRunLifecycle",
]