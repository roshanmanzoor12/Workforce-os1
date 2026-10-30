from __future__ import annotations


PHASE_11_7_TENANT_CONTRACT = {
    "control_plane": {
        "identity": "User",
        "authorization": "WorkspaceMembership",
        "database": "workforce_control",
    },
    "tenant_plane": {
        "organization": [
            "Department",
            "Team",
            "Employee",
        ],
        "attendance": [
            "AttendanceRecord",
            "AttendanceEvent",
        ],
    },
    "routing": {
        "frontend_selects_workspace": True,
        "frontend_selects_database": False,
        "backend_resolves_tenant": True,
        "registered_resolver_required": True,
    },
    "authorization": {
        "reads_require_active_membership": True,
        "organization_mutations": [
            "owner",
            "admin",
        ],
        "attendance_admin_mutations": [
            "owner",
            "admin",
        ],
    },
    "identity_boundaries": {
        "User": "control_plane",
        "WorkspaceMembership": "control_plane",
        "Employee": "tenant_plane",
    },
    "privacy": {
        "keylogging": False,
        "clipboard_capture": False,
        "typed_text_capture": False,
        "password_capture": False,
        "mouse_coordinates": False,
    },
}


__all__ = [
    "PHASE_11_7_TENANT_CONTRACT",
]