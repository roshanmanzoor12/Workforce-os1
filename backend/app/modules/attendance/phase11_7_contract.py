from __future__ import annotations


PHASE_11_7_ATTENDANCE_CONTRACT = {
    "record_table": "attendance_records",
    "event_table": "attendance_events",
    "record_identity": [
        "id",
        "employee_id",
        "attendance_date",
    ],
    "record_timing": [
        "check_in_at",
        "check_out_at",
        "worked_minutes",
        "break_minutes",
    ],
    "record_audit": [
        "created_by_user_id",
        "updated_by_user_id",
        "created_at",
        "updated_at",
    ],
    "event_identity": [
        "id",
        "attendance_record_id",
        "employee_id",
    ],
    "event_audit": [
        "source",
        "actor_user_id",
        "created_at",
        "updated_at",
    ],
    "event_types": [
        "check_in",
        "check_out",
        "break_start",
        "break_end",
    ],
    "sources": [
        "manual",
        "web",
        "desktop_agent",
        "import",
        "system",
    ],
}


__all__ = [
    "PHASE_11_7_ATTENDANCE_CONTRACT",
]