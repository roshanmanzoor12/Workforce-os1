from __future__ import annotations

from decimal import Decimal

from app.modules.leave.models import (
    LeaveBalance,
    LeavePolicy,
    LeaveRequest,
    LeaveRequestStatus,
    LeaveType,
)


def test_leave_request_status_contract():
    assert (
        LeaveRequestStatus.PENDING.value
        == "pending"
    )

    assert (
        LeaveRequestStatus.APPROVED.value
        == "approved"
    )

    assert (
        LeaveRequestStatus.REJECTED.value
        == "rejected"
    )

    assert (
        LeaveRequestStatus.CANCELLED.value
        == "cancelled"
    )


def test_leave_type_table():
    assert (
        LeaveType.__tablename__
        == "leave_types"
    )


def test_leave_policy_table():
    assert (
        LeavePolicy.__tablename__
        == "leave_policies"
    )


def test_leave_balance_table():
    assert (
        LeaveBalance.__tablename__
        == "leave_balances"
    )


def test_leave_request_table():
    assert (
        LeaveRequest.__tablename__
        == "leave_requests"
    )


def test_balance_available_days():
    balance = LeaveBalance(
        allocated_days=(
            Decimal("20")
        ),
        carried_forward_days=(
            Decimal("3")
        ),
        adjustment_days=(
            Decimal("2")
        ),
        used_days=(
            Decimal("5")
        ),
        pending_days=(
            Decimal("4")
        ),
    )

    assert (
        balance.available_days
        == Decimal("16")
    )


def test_request_employee_fk_contract():
    employee_column = (
        LeaveRequest
        .__table__
        .c
        .employee_id
    )

    foreign_keys = list(
        employee_column.foreign_keys
    )

    assert len(
        foreign_keys
    ) == 1

    assert (
        foreign_keys[0]
        .target_fullname
        == "employees.id"
    )


def test_balance_unique_constraint():
    names = {
        constraint.name
        for constraint
        in (
            LeaveBalance
            .__table__
            .constraints
        )
        if constraint.name
    }

    assert (
        "uq_leave_balances_"
        "employee_type_year"
        in names
    )