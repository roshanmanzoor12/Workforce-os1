from __future__ import annotations

import inspect
import uuid
from datetime import date
from decimal import Decimal

from app.modules.payroll.attendance_source import (
    _number,
)
from app.modules.payroll.router import (
    router,
)
from app.modules.payroll.source_schemas import (
    PayrollAdjustmentSource,
    PayrollAttendanceSource,
    PayrollEmployeeSourceBundle,
    PayrollLeaveSource,
    PayrollScheduleDaySource,
    PayrollScheduleSource,
)


def route_paths():
    return {
        route.path
        for route in router.routes
        if hasattr(
            route,
            "path",
        )
    }


def test_calculate_route_is_exposed():
    assert (
        "/workspaces/{workspace_id}"
        "/payroll/runs/{run_id}/calculate"
        in route_paths()
    )


def test_browser_calculate_request_has_no_money_fields():
    from app.modules.payroll.source_schemas import (
        PayrollCalculateRequest,
    )

    fields = set(
        PayrollCalculateRequest
        .model_fields
    )

    assert fields == {
        "employee_ids",
    }


def test_attendance_number_normalizer():
    assert (
        _number(
            {
                "worked_minutes": 480,
            },
            (
                "worked_minutes",
            ),
        )
        == 480
    )


def test_source_snapshot_contains_authoritative_ids():
    employee_id = uuid.uuid4()

    contract_id = uuid.uuid4()

    bundle = (
        PayrollEmployeeSourceBundle(
            employee_id=employee_id,
            compensation_contract_id=(
                contract_id
            ),
            schedule=(
                PayrollScheduleSource(
                    employee_id=employee_id,
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
                    scheduled_minutes=480,
                    payable_minutes=480,
                    days=[
                        PayrollScheduleDaySource(
                            schedule_date=date(
                                2026,
                                9,
                                1,
                            ),
                            source=(
                                "employee_assignment"
                            ),
                            scheduled_minutes=480,
                            payable_minutes=480,
                            is_working_day=True,
                            is_published=True,
                        )
                    ],
                )
            ),
            attendance=(
                PayrollAttendanceSource(
                    employee_id=employee_id,
                    actual_work_minutes=480,
                    overtime_minutes=0,
                    attendance_source_ids=[
                        "attendance-1"
                    ],
                )
            ),
            leave=(
                PayrollLeaveSource(
                    employee_id=employee_id,
                    paid_leave_minutes=0,
                    unpaid_leave_minutes=0,
                    leave_request_ids=[],
                )
            ),
            adjustments=(
                PayrollAdjustmentSource(
                    employee_id=employee_id,
                    additions_total=Decimal(
                        "0"
                    ),
                    deductions_total=Decimal(
                        "0"
                    ),
                    adjustment_ids=[],
                )
            ),
        )
    )

    snapshot = (
        bundle.source_snapshot()
    )

    assert (
        snapshot[
            "compensation_contract_id"
        ]
        == str(
            contract_id
        )
    )

    assert (
        snapshot[
            "schedule"
        ][
            "days"
        ][0][
            "is_published"
        ]
        is True
    )


def test_calculation_service_loads_server_sources():
    from app.modules.payroll.calculation_service import (
        PayrollCalculationService,
    )

    source = inspect.getsource(
        PayrollCalculationService
    )

    assert (
        "PayrollSourceAssembler"
        in source
    )

    assert (
        "PayrollCalculationInput"
        in source
    )

    assert (
        "source_snapshot"
        in source
    )


def test_source_assembler_uses_all_domains():
    from app.modules.payroll.source_assembler import (
        PayrollSourceAssembler,
    )

    source = inspect.getsource(
        PayrollSourceAssembler
    )

    assert (
        "PayrollScheduleSourceService"
        in source
    )

    assert (
        "PayrollAttendanceSourceService"
        in source
    )

    assert (
        "PayrollLeaveSourceService"
        in source
    )

    assert (
        "list_adjustments"
        in source
    )


def test_schedule_source_requires_publication():
    from app.modules.payroll.schedule_source import (
        PayrollScheduleSourceService,
    )

    source = inspect.getsource(
        PayrollScheduleSourceService
    )

    assert (
        "is_published"
        in source
    )

    assert (
        "HTTP_409_CONFLICT"
        in source
    )


def test_leave_source_requires_approved_leave():
    from app.modules.payroll.leave_source import (
        PayrollLeaveSourceService,
    )

    source = inspect.getsource(
        PayrollLeaveSourceService
    )

    assert (
        "LeaveRequestStatus"
        in source
    )

    assert (
        "APPROVED"
        in source
    )

    assert (
        "is_paid"
        in source
    )


def test_calculation_is_audited():
    from app.modules.payroll.audit import (
        PayrollAuditService,
    )

    source = inspect.getsource(
        PayrollAuditService
    )

    assert (
        "payroll.run.calculated"
        in source
    )