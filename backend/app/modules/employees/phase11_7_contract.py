from __future__ import annotations


PHASE_11_7_EMPLOYEE_CONTRACT = {
    "control_plane": {
        "identity": "User",
        "authorization": "WorkspaceMembership",
    },
    "tenant_plane": {
        "organization": [
            "Department",
            "Team",
        ],
        "workforce_identity": "Employee",
    },
    "relationships": {
        "user_to_membership": (
            "control_database"
        ),
        "employee_to_user": (
            "logical_uuid_reference"
        ),
        "employee_to_department": (
            "tenant_foreign_key"
        ),
        "employee_to_team": (
            "tenant_foreign_key"
        ),
        "employee_to_manager": (
            "tenant_self_foreign_key"
        ),
    },
    "rules": {
        "employee_without_user": True,
        "cross_database_foreign_keys": False,
        "browser_selects_database": False,
        "backend_resolves_tenant": True,
    },
}


__all__ = [
    "PHASE_11_7_EMPLOYEE_CONTRACT",
]